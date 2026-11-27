# Reporte Técnico de Optimización y Resultados Experimentales

## 1. Resumen de Instancias Experimentales (Sección 13)

| Instancia | Centros | Zonas | Tipos | Variables | Restricciones | Tiempo (s) | Valor Objetivo | Cobertura (%) | Demanda No Satisfecha | Costo Transporte | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Pequeña | 3 | 5 | 3 | 60 | 42 | 0.02335 | 3220.1624 | 50.0% | 1038.0 | 8376.0 | Optimal |
| Mediana | 5 | 12 | 5 | 360 | 150 | 0.02366 | 12255.3446 | 50.01% | 3067.0 | 36554.0 | Optimal |
| Grande | 10 | 25 | 8 | 2200 | 540 | 0.1549 | 34615.0173 | 49.98% | 9924.0 | 59827.0 | Optimal |

## 2. Análisis Reducido de Branch and Bound (Sección 14)

- **Instancia:** 1 Centro (`Centro 1`, inventario = 5, capacidad = 5), 2 Zonas (`Zona 1` Crítica p=4, demanda=3; `Zona 2` Media p=2, demanda=4), 1 ayuda indivisible (`Kit de mercado`).
- **Formulación entera:** Maximizar $Z = 4x_1 + 2x_2 - 0.0001(2x_1 + 3x_2)$ sujeto a $x_1 + x_2 \le 5$, $0 \le x_1 \le 3$, $0 \le x_2 \le 4$, $x_1, x_2 \in \mathbb{Z}_{\ge 0}$.
- **Relajación lineal (Nodo Raíz):** Al asignar primero a la variable de mayor coeficiente ($x_1 = 3$) y el remanente a $x_2 = 2$, se obtiene una solución entera directamente en la raíz ($x_1 = 3, x_2 = 2$), con cota superior igual a la cota inferior incumbente.
- **Verificación del Solver Automático:** Estado = `Optimal`, Valor Objetivo = `15.9988`, Cobertura Global = `71.43%`, Envíos por zona = `{'Zona 1': {'Kit de mercado': 3.0}, 'Zona 2': {'Kit de mercado': 2.0}}`.
