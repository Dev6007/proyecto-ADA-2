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
    for c in esc["centros"]:
        if c["capacidad"] is not None and c["capacidad"] < 0:
            err.append(f"Centro {c['nombre']}: capacidad negativa.")
        for a, v in c["inventario"].items():
            if v < 0:
                err.append(f"Centro {c['nombre']}: inventario negativo de {a}.")
