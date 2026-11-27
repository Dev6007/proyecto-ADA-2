import json
import csv
import os
from instancias import generar_instancia, TAMANOS
from optimizador import resolver_escenario


def ejecutar_experimentos(carpeta_salida: str = "resultados") -> list:
    os.makedirs(carpeta_salida, exist_ok=True)
    resumen_experimentos = []

    for nombre_tam, (nc, nz, na) in TAMANOS.items():
        esc = generar_instancia(nc, nz, na, seed=1)
        res = resolver_escenario(esc)

        # Guardar escenario y resultado detallado en JSON
        with open(os.path.join(carpeta_salida, f"escenario_{nombre_tam.lower()}.json"), "w", encoding="utf-8") as f:
            json.dump(esc, f, indent=2, ensure_ascii=False)
        with open(os.path.join(carpeta_salida, f"resultado_{nombre_tam.lower()}.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)

        resumen_experimentos.append({
            "Instancia": nombre_tam,
            "Centros": nc,
            "Zonas": nz,
            "Tipos_Ayuda": na,
            "Variables": res["num_variables"],
            "Restricciones": res["num_restricciones"],
            "Tiempo_seg": res["tiempo_solucion_seg"],
            "Valor_Objetivo": res["valor_objetivo"],
            "Cobertura_Global_pct": res["cobertura_global_pct"],
            "Demanda_No_Satisfecha": res["demanda_no_atendida_total"],
            "Costo_Transporte": res["costo_total_transporte"],
            "Estado": res["estado_solucion"],
        })

    # Exportar tabla resumen en CSV
    csv_path = os.path.join(carpeta_salida, "resumen_experimentos.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(resumen_experimentos[0].keys()))
        writer.writeheader()
        writer.writerows(resumen_experimentos)

    return resumen_experimentos


def instancia_reducida_bnb() -> dict:
    """
    Instancia reducida verificada tanto manualmente con Branch and Bound
    como mediante el solver MILP automático.
    """
    esc_bnb = {
        "ayudas": [{"nombre": "Kit de mercado", "indivisible": True}],
        "prioridades": {"Crítica": 4, "Media": 2},
        "centros": [
            {
                "nombre": "Centro 1",
                "activo": True,
                "capacidad": 5,
                "inventario": {"Kit de mercado": 5},
            }
        ],
        "zonas": [
            {
                "nombre": "Zona 1",
                "poblacion": 300,
                "prioridad": "Crítica",
                "min_cobertura": 0.0,
                "demanda": {"Kit de mercado": 3},
            },
            {
                "nombre": "Zona 2",
                "poblacion": 400,
                "prioridad": "Media",
                "min_cobertura": 0.0,
                "demanda": {"Kit de mercado": 4},
            },
        ],
        "rutas": [
            {"centro": "Centro 1", "zona": "Zona 1", "disponible": True, "costo": 2, "capacidad": 5},
            {"centro": "Centro 1", "zona": "Zona 2", "disponible": True, "costo": 3, "capacidad": 5},
        ],
        "restricciones": {"presupuesto": None},
    }
    res_bnb = resolver_escenario(esc_bnb)
    return {"escenario": esc_bnb, "resultado_solver": res_bnb}


def generar_reporte_markdown(resumen: list, bnb_data: dict, ruta_md: str = "resultados/REPORTE_OPTIMIZACION.md") -> str:
    os.makedirs(os.path.dirname(ruta_md), exist_ok=True)
    res_bnb = bnb_data["resultado_solver"]

    lineas = [
        "# Reporte Técnico de Optimización y Resultados Experimentales",
        "",
        "## 1. Resumen de Instancias Experimentales (Sección 13)",
        "",
        "| Instancia | Centros | Zonas | Tipos | Variables | Restricciones | Tiempo (s) | Valor Objetivo | Cobertura (%) | Demanda No Satisfecha | Costo Transporte | Estado |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in resumen:
        lineas.append(
            f"| {r['Instancia']} | {r['Centros']} | {r['Zonas']} | {r['Tipos_Ayuda']} | "
            f"{r['Variables']} | {r['Restricciones']} | {r['Tiempo_seg']} | {r['Valor_Objetivo']} | "
            f"{r['Cobertura_Global_pct']}% | {r['Demanda_No_Satisfecha']} | {r['Costo_Transporte']} | {r['Estado']} |"
        )

    lineas.extend([
        "",
        "## 2. Análisis Reducido de Branch and Bound (Sección 14)",
        "",
        "- **Instancia:** 1 Centro (`Centro 1`, inventario = 5, capacidad = 5), 2 Zonas (`Zona 1` Crítica p=4, demanda=3; `Zona 2` Media p=2, demanda=4), 1 ayuda indivisible (`Kit de mercado`).",
        "- **Formulación entera:** Maximizar $Z = 4x_1 + 2x_2 - 0.0001(2x_1 + 3x_2)$ sujeto a $x_1 + x_2 \le 5$, $0 \le x_1 \le 3$, $0 \le x_2 \le 4$, $x_1, x_2 \in \mathbb{Z}_{\ge 0}$.",
        "- **Relajación lineal (Nodo Raíz):** Al asignar primero a la variable de mayor coeficiente ($x_1 = 3$) y el remanente a $x_2 = 2$, se obtiene una solución entera directamente en la raíz ($x_1 = 3, x_2 = 2$), con cota superior igual a la cota inferior incumbente.",
        f"- **Verificación del Solver Automático:** Estado = `{res_bnb['estado_solucion']}`, Valor Objetivo = `{res_bnb['valor_objetivo']}`, Cobertura Global = `{res_bnb['cobertura_global_pct']}%`, Envíos por zona = `{res_bnb['recibido_por_zona']}`.",
        "",
    ])

    contenido = "\n".join(lineas)
    with open(ruta_md, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta_md


if __name__ == "__main__":
    resumen = ejecutar_experimentos("resultados")
    bnb = instancia_reducida_bnb()
    ruta_md = generar_reporte_markdown(resumen, bnb, "resultados/REPORTE_OPTIMIZACION.md")
    print("Experimentos ejecutados correctamente. Reporte generado en:", ruta_md)
    for fila in resumen:
        print(fila)
