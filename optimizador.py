import time
from ortools.linear_solver import pywraplp
from validacion import validar


def resolver_escenario(esc: dict, lambda_costo: float = 1e-4) -> dict:
    """
    Construye y resuelve el modelo MILP de distribución de ayudas humanitarias
    usando Google OR-Tools (SCIP), compatible con instancias.py y validacion.py.
    """
    errores = validar(esc)
    if errores:
        raise ValueError("Escenario inválido:\n- " + "\n- ".join(errores))

    t0 = time.perf_counter()

    ayudas_info = {a["nombre"]: a for a in esc["ayudas"]}
    centros_info = {c["nombre"]: c for c in esc["centros"]}
    zonas_info = {z["nombre"]: z for z in esc["zonas"]}
    prioridades = esc["prioridades"]

    A = list(ayudas_info.keys())
    C = list(centros_info.keys())
    Z = list(zonas_info.keys())

    rutas_map = {}
    for r in esc["rutas"]:
        rutas_map[(r["centro"], r["zona"])] = r
    E = list(rutas_map.keys())

    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        raise RuntimeError("No se pudo inicializar el solver MILP (SCIP/CBC) en OR-Tools.")

    inf = solver.infinity()

    # Variables de decisión:
    # x[c, z, a]: cantidad enviada de ayuda 'a' desde centro 'c' hacia zona 'z'
    x = {}
    for (c, z) in E:
        ruta = rutas_map[(c, z)]
        disp = bool(ruta.get("disponible", True))
        cap_ruta = ruta.get("capacidad", None)
        for a in A:
            indivisible = bool(ayudas_info[a].get("indivisible", True))
            up_bound = 0.0 if not disp else (float(cap_ruta) if cap_ruta is not None else inf)
            nombre_var = f"x_{c}_{z}_{a}".replace(" ", "_")
            if indivisible:
                x[(c, z, a)] = solver.IntVar(0.0, up_bound, nombre_var)
            else:
                x[(c, z, a)] = solver.NumVar(0.0, up_bound, nombre_var)

    # u[z, a]: demanda no satisfecha de ayuda 'a' en zona 'z'
    u = {}
    for z in Z:
        zona = zonas_info[z]
        min_cob = float(zona.get("min_cobertura", 0.0))
        for a in A:
            dem_za = float(zona["demanda"].get(a, 0.0))
            max_no_atendida = dem_za * (1.0 - min_cob)
            nombre_u = f"u_{z}_{a}".replace(" ", "_")
            u[(z, a)] = solver.NumVar(0.0, max_no_atendida, nombre_u)

    # Restricción 1: Balance de demanda y demanda parcialmente insatisfecha
    for z in Z:
        for a in A:
            dem_za = float(zonas_info[z]["demanda"].get(a, 0.0))
            ct = solver.Constraint(dem_za, dem_za, f"BalanceDem_{z}_{a}".replace(" ", "_"))
            for (c, dest) in E:
                if dest == z:
                    ct.SetCoefficient(x[(c, z, a)], 1.0)
            ct.SetCoefficient(u[(z, a)], 1.0)

    # Restricción 2 y 3: Inventario disponible, estado activo y capacidad máxima de despacho del centro
    for c in C:
        centro = centros_info[c]
        activo = 1.0 if centro.get("activo", True) else 0.0
        for a in A:
            inv_ca = activo * float(centro["inventario"].get(a, 0.0))
            ct_inv = solver.Constraint(-inf, inv_ca, f"Inv_{c}_{a}".replace(" ", "_"))
            for (orig, z) in E:
                if orig == c:
                    ct_inv.SetCoefficient(x[(c, z, a)], 1.0)

        cap_c = centro.get("capacidad", None)
        if cap_c is not None:
            ct_cap_c = solver.Constraint(-inf, activo * float(cap_c), f"CapCentro_{c}".replace(" ", "_"))
            for (orig, z) in E:
                if orig == c:
                    for a in A:
                        ct_cap_c.SetCoefficient(x[(c, z, a)], 1.0)

    # Restricción 4 y 5: Capacidad máxima de transporte y bloqueo de rutas
    for (c, z) in E:
        ruta = rutas_map[(c, z)]
        disp = 1.0 if ruta.get("disponible", True) else 0.0
        cap_ruta = ruta.get("capacidad", None)
        if cap_ruta is not None:
            ct_r = solver.Constraint(-inf, disp * float(cap_ruta), f"CapRuta_{c}_{z}".replace(" ", "_"))
            for a in A:
                ct_r.SetCoefficient(x[(c, z, a)], 1.0)
        elif disp == 0.0:
            ct_r = solver.Constraint(0.0, 0.0, f"BloqRuta_{c}_{z}".replace(" ", "_"))
            for a in A:
                ct_r.SetCoefficient(x[(c, z, a)], 1.0)

    # Restricción adicional opcional: Presupuesto global de transporte
    presupuesto = esc.get("restricciones", {}).get("presupuesto", None)
    if presupuesto is not None:
        ct_pres = solver.Constraint(-inf, float(presupuesto), "PresupuestoGlobal")
        for (c, z) in E:
            costo_r = float(rutas_map[(c, z)]["costo"])
            for a in A:
                ct_pres.SetCoefficient(x[(c, z, a)], costo_r)

    # Función objetivo:
    # Maximizar sum_{z,a} p_z * (dem_{z,a} - u_{z,a}) - lambda_costo * sum_{c,z,a} costo_{c,z} * x_{c,z,a}
    objetivo = solver.Objective()
    constante_dem = 0.0
    for z in Z:
        pz = float(prioridades[zonas_info[z]["prioridad"]])
        for a in A:
            dem_za = float(zonas_info[z]["demanda"].get(a, 0.0))
            constante_dem += pz * dem_za
            objetivo.SetCoefficient(u[(z, a)], -pz)

    for (c, z) in E:
        costo_r = float(rutas_map[(c, z)]["costo"])
        for a in A:
            objetivo.SetCoefficient(x[(c, z, a)], -lambda_costo * costo_r)

    objetivo.SetOffset(constante_dem)
    objetivo.SetMaximization()

    status = solver.Solve()
    tiempo_seg = time.perf_counter() - t0

    mapa_estados = {
        pywraplp.Solver.OPTIMAL: "Optimal",
        pywraplp.Solver.FEASIBLE: "Feasible",
        pywraplp.Solver.INFEASIBLE: "Infeasible",
        pywraplp.Solver.UNBOUNDED: "Unbounded",
        pywraplp.Solver.ABNORMAL: "Abnormal",
        pywraplp.Solver.NOT_SOLVED: "Not Solved",
    }
    estado_solucion = mapa_estados.get(status, f"Status_{status}")

    enviado_por_centro = {c: {a: 0.0 for a in A} for c in C}
    total_enviado_centro = {c: 0.0 for c in C}
    recibido_por_zona = {z: {a: 0.0 for a in A} for z in Z}
    rutas_utilizadas = []
    costo_total = 0.0

    inventario_restante = {
        c: {a: float(centros_info[c]["inventario"].get(a, 0.0)) for a in A}
        for c in C
    }

    for (c, z) in E:
        envios_ruta = {}
        total_ruta = 0.0
        costo_unitario = float(rutas_map[(c, z)]["costo"])
        for a in A:
            val = float(x[(c, z, a)].solution_value()) if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else 0.0
            if ayudas_info[a].get("indivisible", True):
                val = round(val)
            if val > 1e-6:
                envios_ruta[a] = val
                total_ruta += val
                enviado_por_centro[c][a] += val
                total_enviado_centro[c] += val
                recibido_por_zona[z][a] += val
                inventario_restante[c][a] = round(inventario_restante[c][a] - val, 4)
                costo_total += val * costo_unitario
        if total_ruta > 1e-6:
            rutas_utilizadas.append({
                "centro": c,
                "zona": z,
                "total_unidades": round(total_ruta, 4),
                "costo_ruta": round(total_ruta * costo_unitario, 2),
                "detalle": envios_ruta,
            })

    demanda_atendida_zona = {}
    demanda_no_atendida_zona = {}
    cobertura_por_zona = {}
    dem_global = 0.0
    at_global = 0.0

    for z in Z:
        dem_z = sum(float(zonas_info[z]["demanda"].get(a, 0.0)) for a in A)
        at_z = sum(recibido_por_zona[z][a] for a in A)
        no_at_z = sum(float(u[(z, a)].solution_value()) for a in A) if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else dem_z
        demanda_atendida_zona[z] = round(at_z, 4)
        demanda_no_atendida_zona[z] = round(no_at_z, 4)
        cobertura_por_zona[z] = round((at_z / dem_z * 100.0) if dem_z > 0 else 100.0, 2)
        dem_global += dem_z
        at_global += at_z

    demanda_atendida_ayuda = {}
    demanda_no_atendida_ayuda = {}
    cobertura_por_ayuda = {}

    for a in A:
        dem_a = sum(float(zonas_info[z]["demanda"].get(a, 0.0)) for z in Z)
        at_a = sum(recibido_por_zona[z][a] for z in Z)
        no_at_a = sum(float(u[(z, a)].solution_value()) for z in Z) if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else dem_a
        demanda_atendida_ayuda[a] = round(at_a, 4)
        demanda_no_atendida_ayuda[a] = round(no_at_a, 4)
        cobertura_por_ayuda[a] = round((at_a / dem_a * 100.0) if dem_a > 0 else 100.0, 2)

    cobertura_global = round((at_global / dem_global * 100.0) if dem_global > 0 else 100.0, 2)
    demanda_no_atendida_total = round(sum(demanda_no_atendida_ayuda.values()), 4)
    val_obj = round(float(objetivo.Value()), 4) if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else 0.0

    return {
        "estado_solucion": estado_solucion,
        "valor_objetivo": val_obj,
        "tiempo_solucion_seg": round(tiempo_seg, 5),
        "num_variables": solver.NumVariables(),
        "num_restricciones": solver.NumConstraints(),
        "cobertura_global_pct": cobertura_global,
        "cobertura_por_zona_pct": cobertura_por_zona,
        "cobertura_por_ayuda_pct": cobertura_por_ayuda,
        "enviado_por_centro": enviado_por_centro,
        "total_enviado_centro": total_enviado_centro,
        "recibido_por_zona": recibido_por_zona,
        "demanda_atendida_zona": demanda_atendida_zona,
        "demanda_no_atendida_zona": demanda_no_atendida_zona,
        "demanda_atendida_ayuda": demanda_atendida_ayuda,
        "demanda_no_atendida_ayuda": demanda_no_atendida_ayuda,
        "demanda_no_atendida_total": demanda_no_atendida_total,
        "rutas_utilizadas": rutas_utilizadas,
        "costo_total_transporte": round(costo_total, 2),
        "inventario_restante": inventario_restante,
    }
