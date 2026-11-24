import random

def generar_instancia(nc, nz, na, seed=1):
    rnd = random.Random(seed)
    base = ["Kit de mercado", "Agua", "Kit de aseo", "Kit de cocina", "Kit de descanso",
            "Kit de la primera infancia", "Medicinas", "Abrigo"]
    A = [base[i] if i < len(base) else f"Ayuda {i+1}" for i in range(na)]
    centros = []
    for i in range(nc):
        inv = {a: rnd.randint(50, 300) for a in A}
        centros.append(dict(nombre=f"Centro {i+1}", activo=True,
                            capacidad=round(0.7 * sum(inv.values())), inventario=inv))
    prios = {"Crítica": 4, "Alta": 3, "Media": 2, "Baja": 1}
    zonas = []
    for j in range(nz):
        pop = rnd.randint(200, 5000)
        zonas.append(dict(nombre=f"Zona {j+1}", poblacion=pop, prioridad=rnd.choice(list(prios)),
                          min_cobertura=0.0, demanda={a: pop * rnd.uniform(0.05, 0.15) for a in A}))
    for a in A:  # <-- Para evidenciar la escasez nos paramos aqui 
        oferta = sum(c["inventario"][a] for c in centros)
        tot = sum(z["demanda"][a] for z in zonas)
        for z in zonas:
            z["demanda"][a] = max(1, round(z["demanda"][a] * 1.4 * oferta / tot))
    rutas = [dict(centro=c["nombre"], zona=z["nombre"], disponible=rnd.random() > 0.1,
                  costo=rnd.randint(1, 20), capacidad=rnd.randint(100, 400))
             for c in centros for z in zonas]
    return dict(ayudas=[dict(nombre=a, indivisible=(a != "Agua")) for a in A], prioridades=prios,
                centros=centros, zonas=zonas, rutas=rutas, restricciones=dict(presupuesto=None))


TAMANOS = {"Pequeña": (3, 5, 3), "Mediana": (5, 12, 5), "Grande": (10, 25, 8)}
