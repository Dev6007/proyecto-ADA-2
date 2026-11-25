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
