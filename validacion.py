def validar(esc):
    err = []
    nombres = lambda l: [e["nombre"] for e in l]
    for clave in ("ayudas", "centros", "zonas"):
        n = nombres(esc[clave])
        if not n:
            err.append(f"Aqui debe existir al menos un elemento en '{clave}'.")
        if len(set(n)) != len(n) or "" in n:
            err.append(f"Nombres vacios o repetidos en '{clave}'.")
    A, C, Z = nombres(esc["ayudas"]), nombres(esc["centros"]), nombres(esc["zonas"])
    for c in esc["centros"]: # <-- validacion de centros
        if c["capacidad"] is not None and c["capacidad"] < 0:
            err.append(f"Centro {c['nombre']}: capacidad negativa.")
        for a, v in c["inventario"].items():
            if v < 0:
                err.append(f"Centro {c['nombre']}: inventario negativo de {a}.")
    for z in esc["zonas"]: # <-- validacion de zonas
        if z["prioridad"] not in esc["prioridades"]:
            err.append(f"Zona {z['nombre']}: prioridad '{z['prioridad']}' no definida.")
        if any(v < 0 for v in z["demanda"].values()) or z["poblacion"] < 0:
            err.append(f"Zona {z['nombre']}: valores negativos.")
        if not 0 <= z["min_cobertura"] <= 1:
            err.append(f"Zona {z['nombre']}: cobertura mínima debe estar entre 0 y 100 %.")
    for r in esc["rutas"]: # <-- validacion de rutas
        if r["centro"] not in C or r["zona"] not in Z:
            err.append(f"Ruta {r['centro']}→{r['zona']}: centro o zona inexistente.")
        if r["costo"] < 0 or (r["capacidad"] is not None and r["capacidad"] < 0):
            err.append(f"Ruta {r['centro']}→{r['zona']}: costo/capacidad negativos.")
    if any(w < 0 for w in esc["prioridades"].values()):
        err.append("Los pesos de prioridad no pueden ser negativos.")
    return err
