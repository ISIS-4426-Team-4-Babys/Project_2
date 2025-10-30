# Plan y Resultados de Pruebas de Carga 

## 1. Introducción

El presente documento describe las pruebas de carga realizadas sobre la aplicación de agentes conversacionales, con el objetivo de evaluar el rendimiento y estabilidad de la arquitectura montada en el playground de AWS bajo escenarios de carga concurrente. Se evaluaron dos tareas principales:

1. Creación y despliegue de un nuevo agente a partir de un documento base. 
2. Interacción conversacional (envío de preguntas) a un agente desplegado a partir de un documento base. 

Cada tarea se sometió a tres escenarios de carga, con variaciones en la cantidad de usuarios, el ritmo de llegada o ingreso de los usuarios al sistema y el número de peticiones por usuario.

---

## 2. Objetivos

- Medir la capacidad del sistema para manejar múltiples peticiones concurrentes sin errores.
- Evaluar la latencia promedio, distribución de tiempos de respuesta y estabilidad de los dos servicios críticos de la aplicación.
- Identificar posibles cuellos de botella durante el proceso de creación y comunicación con los agentes.
- Obtener métricas que permitan proyectar la escalabilidad del sistema en entornos de uso real o cercano al real.

---

## 3. Alcance

Las pruebas se centraron en los endpoints principales de la aplicación:

- `POST /resources` → Creación y despliegue de agentes. Intervienen más endpoints pero el referenciado es el que desata la mayor cantidad de procesamiento asíncrono y señaliza el inicio del proceso de creación del agente.  
- `POST /ask` → Envío de preguntas a un agente ya desplegado a partir de un documento base. 

Las pruebas se realizaron sobre un entorno controlado, replicando escenarios de uso real sin interferencia de otras cargas externas.

---

## 4. Herramientas y Entorno

Para la evaluación del rendimiento se utilizó la herramienta Locust
, una plataforma de carga y estrés que permite simular múltiples usuarios concurrentes realizando peticiones HTTP. Esta herramienta facilitó la medición de métricas clave como el tiempo promedio de respuesta, los percentiles de latencia (P50, P90, P99), el porcentaje de fallos y la tasa de peticiones por segundo (Req/s).

Las pruebas se llevaron a cabo en el Playground de AWS, utilizando instancias dedicadas que no ejecutaban procesos adicionales capaces de introducir carga significativa o interferir con los resultados. Es importante resaltar que las pruebas se realizaron sin aceleración por GPU, por lo que todos los tiempos de inferencia y despliegue corresponden únicamente al procesamiento en CPU.

---

## 5. Escenarios de Prueba

Cada tarea fue probada en tres escenarios idénticos en estructura, variando solo el endpoint.

| Escenario | Descripción | Usuarios totales | Ramp-up | Repeticiones por usuario | Intervalo entre peticiones |
|------------|-------------|------------------|----------|---------------------------|-----------------------------|
| 1 | Usuario único enviando 10 peticiones consecutivas con 10 s entre cada una (contados desde el éxito o resolución de la petición) | 1 | N/A | 10 | 10 s |
| 2 | Carga concurrente progresiva con 10 usuarios, aumento de 2 usuarios/s | 10 | 2 usuarios/s | 1 | N/A |
| 3 | Carga instantánea con 10 usuarios simultáneos | 10 | 10 usuarios/s | 1 | N/A |

---

## 6. Métricas Evaluadas

- **Avg:** Tiempo promedio de respuesta o despliegue (ms o s, dependiendo de la tarea evaluada).
- **Min / Max:** Tiempos mínimo y máximo observados durante el desarrollo de la prueba de carga.
- **Mediana (p50):** Punto medio de distribución, específicamente para la prueba de chat, donde el tiempo de respuesta del endpoint refleja el rendimiento real. 
- **Percentiles (p90, p95, p99):** Medidas de dispersión, específicamente para la prueba de chat, donde el tiempo de respuesta del endpoint refleja el rendimiento real.
- **Fails (%):** Porcentaje de peticiones fallidas.
- **Req/s:** Solicitudes procesadas por segundo.
- **Tiempo de despliegue:** Para la tarea de creación, tiempo total entre inicio y fin del despliegue, dada la complejidad de su naturaleza asincrónica. 

---

## 7. Resultados y Análisis

### 7.1. Tarea 1 — Creación y Despliegue de Agentes

#### Escenario 1 — Usuario único (10 despliegues secuenciales)

| Métrica | Valor |
|----------|--------|
| Tiempo promedio de despliegue | **698.47 s** |
| Tiempo mínimo | 180.30 s |
| Tiempo máximo | 1,444.73 s |
| Diferencia promedio entre despliegues consecutivos | 126.44 s |
| Fallos | 0 % |

**Análisis:**  
El tiempo de despliegue aumenta progresivamente con cada agente, pasando de 3 a 24 minutos por agente. La diferencia promedio entre despliegues (126 s) sugiere un incremento constante en la carga del entorno, justificada por la naturaleza secuencial del proceso y por la ausencia de GPU para aumentar el rendimiento de los modelos. 

---

#### Escenario 2 — 10 usuarios concurrentes (ramp-up de 2/s)

| Métrica | Valor |
|----------|--------|
| Tiempo promedio de despliegue | **854.37 s** |
| Tiempo mínimo | 191.91 s |
| Tiempo máximo | 1,467.67 s |
| Diferencia promedio entre despliegues consecutivos | 127.58 s |
| Fallos | 0 % |

**Análisis:**  
El incremento en la concurrencia produce un aumento leve en el tiempo promedio, aunque el sistema mantiene estabilidad. No se registraron errores, lo que confirma que el servicio puede gestionar la creación paralela de agentes, aunque con una penalización desproporcionada en la latencia del sistema.

---

#### Escenario 3 — 10 usuarios simultáneos (sin ramp-up)

| Métrica | Valor |
|----------|--------|
| Tiempo promedio de despliegue | **738.63 s** |
| Tiempo mínimo | 184.57 s |
| Tiempo máximo | 1,472.05 s |
| Diferencia promedio entre despliegues consecutivos | 128.75 s |
| Fallos | 0 % |

**Análisis:**  
El comportamiento se mantiene similar al escenario anterior, con tiempos ligeramente inferiores en promedio, lo que indica que la creación simultánea no genera degradación significativa. Las diferencias entre agentes permanecen estables, confirmando una vez más el efecto del procesamiento secuencial en los tiempos de despliegue.

---

#### Resumen de tiempos promedio 

| Escenario | Tiempo promedio (s) | Diferencia promedio (s) |
|------------|---------------------|--------------------------|
| 1 | 698.47 | 126.44 |
| 2 | 854.37 | 127.58 |
| 3 | 738.63 | 128.75 |

**Conclusión parcial:**  
El proceso de creación y despliegue es estable, sin errores y con comportamiento predecible, aunque los tiempos de despliegue (10–25 minutos) son altos para uso en producción. Es necesario paralelizar los pasos críticos del proceso, además de agregar capacidad de procesamiento mediante el uso de GPUs para la paralelización y ejecución de los modelos. 

---

### 7.2. Tarea 2 — Chat con Agente Desplegado

#### Escenario 1 — Usuario único (10 peticiones secuenciales)

| Métrica | Valor |
|----------|--------|
| Promedio (Avg) | **150.44 s** |
| Mínimo | 103.85 s |
| Máximo | 197.53 s |
| Mediana (p50) | 158 s |
| p90 | 198 s |
| Fallos | 0 % |

**Análisis:**  
El sistema presenta un rendimiento consistente con un solo usuario, con tiempos estables entre 100 y 200 segundos. La variación moderada indica que la latencia está dominada por el tiempo de respuesta del modelo de lenguaje y la ejecución de los modelos locales de reranking y generación de embeddings. 

---

#### Escenario 2 — 10 usuarios con ramp-up de 2/s

| Métrica | Valor |
|----------|--------|
| Promedio (Avg) | **1119.455 s** |
| Mínimo | 946.30 s |
| Máximo | 1244.35 s |
| Mediana (p50) | 1132 s |
| p90 | 1244 s |
| Fallos | 0 % |

**Análisis:**  
Al incrementar la concurrencia, la latencia promedio se eleva considerablemente, superando el umbral de los diez minutos por respuesta generada. Esto evidencia que tanto el modelo consumido por API como los modelos locales se saturan, y aunque no falla, gastan demasiado tiempo realizando las tareas debido a su poca capacidad de paralelización. 

---

#### Escenario 3 — 10 usuarios simultáneos

| Métrica | Valor |
|----------|--------|
| Promedio (Avg) | **1206.50 s** |
| Mínimo | 973.65 s |
| Máximo | 1402.95 s |
| Mediana (p50) | 1232 s |
| p90 | 1403 s |
| Fallos | 0 % |

**Análisis:**  
Con carga máxima instantánea, la latencia promedio sube ligeramente respecto al escenario anterior, manteniendo estabilidad y sin fallos. De igual forma, se evidencia problemas en el procesamiento paralelo por parte de los modelos, lo que hace que los tiempos sean demasiado elevados. 
---

#### Resumen de tiempos promedio

| Escenario | Tiempo promedio (s) | p90 (s) | Fallos (%) |
|------------|----------------------|-----------|-------------|
| 1 | 150.44 | 198 | 0 |
| 2 | 1119.45 | 1.244 | 0 |
| 3 | 1206.51 | 1.403 | 0 |

**Conclusión parcial:**  
El sistema mantiene su estabilidad bajo carga, pero la latencia crece proporcionalmente con la concurrencia. Los tiempos de respuesta no son aceptables para tareas conversacionales, ya que son demasiado elevados y aumentan cosiderablemente al someterse a carga concurrente por parte de los usuarios. Es necesario paralelizar el proceso de inferencia y contar con capacidad computacional en forma de GPUs para acelerar y paralelizar el procesamiento por parte de los modelos. 

---

## 8. Conclusiones Generales 

1. **Estabilidad comprobada:** Ningún escenario produjo fallos ni errores HTTP, demostrando que la arquitectura es funcional y resistente bajo carga.  
2. **Alta latencia:** La latencia en la creación de agentes y las respuestas del chat son demasiado elevadas para escenarios de uso concurrente e intensivo, afectando considerablemente la experiencia del usuario.  
3. **Escalabilidad:** El sistema escala correctamente con más usuarios, aunque con un crecimiento considerable en los tiempos de respuesta y latencia.  

---
