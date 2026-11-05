# Paleando Menorca

Diario personal de paddle surf. Nueva edición 0.3.0, creada desde cero con HTML, CSS y JavaScript. Sin Cloudflare, sin instalación y sin compilación. El repositorio conserva por ahora el nombre técnico `Palenado-Menorca`.

## Publicación

En **Settings → Pages → Build and deployment**, seleccionar **GitHub Actions** una sola vez. El flujo `.github/workflows/pages.yml` comprobará y publicará los cambios de `main`. Si la primera ejecución se produjo antes de habilitar Pages, repetirla en **Actions → Comprobar y publicar Paleando Menorca → Run workflow**.

Dirección pública: https://javieramudo-arch.github.io/Palenado-Menorca/

## Desarrollo

Requiere Node 22+ para las pruebas y Python 3 para el servidor local.

```sh
npm ci
npm test
npm start
```

Abrir http://localhost:8081. No abrir `index.html` mediante `file://`.

## Backend

Proyecto Supabase nuevo: `akjuzerljejqkizpaotw`, región París. La configuración pública está en `backend.js`; solo contiene la URL y la clave publicable. No contiene credenciales administrativas.

- Autenticación por correo y contraseña. El registro puede requerir confirmar el correo. No usa ChatGPT para entrar.
- `public.entries`: salidas, planes, lugares, objetivos y preferencias, con propiedad por `user_id`, RLS y políticas separadas por operación.
- Control de revisión optimista para detectar fichas cambiadas en otra sesión.
- Bucket privado `photos`, máximo 10 MB por JPG/PNG/WebP, rutas por usuario y lectura mediante enlaces firmados de cinco minutos.
- Borrado lógico con recuperación durante 30 segundos. No se borran los archivos de fotografías al quitar referencias.

Configurar en Supabase **Authentication → URL Configuration** la URL definitiva del sitio y su lista de redirecciones cuando Pages esté habilitado. Esta configuración no se ha cambiado mediante el conector disponible.

## Implementado en código

Mapa Leaflet, tres bases (OpenTopoMap, PNOA, OpenStreetMap), cuatro controles independientes, GPS y radio de precisión, pantalla completa, filtros de recorridos y las cinco categorías de marcadores. Diario con búsqueda, filtro por año y favoritas, trazado costero automático con puntos de paso, edición, rutas pendientes y conversión explícita a salida. Importación GPX con revisión y exportación, distancia geodésica sin duplicar GPX, objetivos anuales, actividad mensual, lugares, fotos privadas, asociación de foto a marcador, estados de guardado y borradores por cuenta. Previsión diaria real de Open-Meteo, con errores visibles y enlace a Windy.

Práctica dirigida de 28 acciones reales, aislada de las escrituras de servidor: mapa, marcador, fotografía de ejemplo, asociación, tiempo, menú, guardar, editar, eliminar y deshacer. Retroceso por puntos de restauración, salida y conversión final a borrador real para revisión. Comienza después del login salvo preferencia “No mostrar de nuevo”; se puede reiniciar desde Ayuda y guía. La preferencia de la guía se recuerda por cuenta en este navegador; Preferencias permite guardarla también en la cuenta.

Miniaturas privadas, acceso al mar, borrador visible, validación de fichas, protección frente a respuestas de otra sesión y paginación del diario. Detalle de hallazgos y límites en [AUDITORIA.md](AUDITORIA.md).

## Pendiente, sin datos inventados

- Alternativa corta/larga. La costa única y el porcentaje ya se calculan como unión de intervalos de las aristas costeras de referencia. La barra principal muestra ese porcentaje, separado de los objetivos anuales.
- La imagen original del logo anterior no está disponible. Se ha creado un logo nuevo inspirado en su descripción.
- Condiciones recomendadas, ritmo y paradas; previsión de oleaje y comparativas entre años.
- Sincronización automática de borradores entre dispositivos. Los borradores se conservan en el navegador de la cuenta y el guardado definitivo requiere conexión.

No se incluye un service worker: los archivos se sirven por Internet para evitar actualizaciones atrapadas en cachés anteriores.

## Verificación

Pruebas unitarias reales en `tests/core.test.js`: distancias, ida y vuelta, exclusión de pendientes y eliminadas, restauración, agregación mensual, exportación y textos no confiables. Sintaxis JavaScript comprobada. La revisión actual confirma RLS y fotografías privadas. El asesor señala protección contra contraseñas filtradas desactivada; ver AUDITORIA.md.

La ejecución local de Chromium está bloqueada por la política del entorno. Las pruebas de navegador de CI, cuando se ejecuten, usarán backend simulado y no equivaldrán a login, fotografías, GPS o sincronización de una cuenta real. Deben comprobarse además tacto, teclado y ventanas en el Redmi Note 9 Pro, previsión real y publicación de Pages antes de considerarlas validadas.

## Servicios externos y atribución

Leaflet 1.9.4 (unpkg), supabase-js 2.57.4 (esm.sh), fuentes DM Sans/Outfit (Google Fonts), OpenStreetMap, OpenTopoMap, IGN/PNOA y Open-Meteo. La cartografía conserva su atribución. El acceso depende de conectividad y disponibilidad de esos proveedores. Los recorridos y previsiones no garantizan navegabilidad.

## Trazado costero

Nueva salida y Planificar ruta ajustan los puntos a la costa principal de Menorca y guardan la polilínea costera completa. Los kilómetros se calculan sumando sus segmentos. Los puntos marcados se guardan aparte para poder quitar el último sin borrar vértices de la costa. No se añaden conectores rectos al cálculo. Se rechazan puntos a más de 1.500 m y puntos que coinciden en la costa. Un GPX se conserva salvo confirmación explícita de sustitución. Las salidas ya guardadas no se recalculan en segundo plano.

Datos: IDEIB · GOIB / SITIBSA · MTIB 2012, escala 1:5.000; geometría simplificada a 2,5 m, 19.137 vértices y 19.136 aristas de la componente principal. Fuente: https://ideib.caib.es/geoserveis/rest/services/public/GOIB_MTIB5m2012_Me/MapServer. El cálculo usa el camino disponible más corto del grafo, sin inventar puentes entre tramos desconectados; no es una garantía de navegabilidad ni incorpora condiciones del mar.


## 0.3 · Costa única y diseño compacto

La cabecera separa kilómetros paleados, costa total de referencia y costa única recorrida. La barra mide el porcentaje de costa única, no el objetivo anual. El total se calcula desde las aristas únicas de la componente principal: actualmente unos 356,39 km en esta geometría detallada; no es una longitud oficial universal ni incluye todos los islotes.

Los recorridos costeros se convierten en intervalos sobre aristas. Se unen los solapamientos entre salidas y recorridos en ambos sentidos. Los fragmentos de arista se cuentan proporcionalmente y no como aristas completas. Ida y vuelta duplica el paleado pero no la cobertura. Eliminar y restaurar recalcula desde las salidas activas; las pendientes y la práctica no alteran el progreso real.

Para GPX se acredita únicamente costa paralela a los segmentos y a menos de 75 m: es una estimación cartográfica, no un trazado costero inferido entre extremos. Los recorridos antiguos sin coincidencias mantienen su distancia paleada y avisan de que no aportan cobertura. No se reescriben datos antiguos.

El bloque de bienvenida se ha eliminado. Fondo SVG con patrón tenue de tablas, palas y olas. Logo nuevo generado a partir de la descripción de los dos palistas y la Jack Russell; no se ha recuperado la imagen original. Objetivos anuales conservados en Progreso, independientes de la barra costera.


## 0.4.0 · Cinco flujos revisados

- Ver aventura abre Mapa por ID, encuadra la geometría con márgenes para los controles, resalta la ruta y muestra su nombre y tipo. Ficha conserva el acceso a sus datos. Las geometrías inválidas muestran un aviso.
- Tiempo requiere elegir un punto. El modo previo se conserva y se restaura al cancelar o cerrar. Consultas horarias independientes a Open-Meteo Forecast y Marine, con temperatura, viento en km/h, dirección de origen, oleaje en metros y dirección de origen. Fecha/hora Europe/Madrid, coordenadas elegidas y ajuste a la celda marítima. Flechas hacia el destino, rótulos del origen. Sin reutilizar datos anteriores. Datos ausentes: No disponible; reintento ante error total o parcial.
- Instalar app en el pie: manifest con iconos PNG 192/512 y service worker de red sin caché de datos privados. Prompt nativo si el navegador lo ofrece; instrucciones específicas en los demás casos; oculto en modo instalado. No es un APK ni se promete funcionamiento sin conexión.
- Pendientes: ritmo editable en min/km (preferencia de cuenta o 15 por defecto), paradas, ida/vuelta y duración estimada en horas/minutos. Cálculo automático y modo manual explícito. Se guarda separada de la duración real; al convertir en salida se solicita duración real nueva. Los valores anteriores de duración de pendientes se preservan como estimación manual al editarlas.
- Colores y etiquetas unificados: realizada solo ida verde, realizada ida/vuelta naranja; cualquier pendiente azul, también en vista previa y fichas.

Esta entrega ejecuta únicamente tests/features.test.js, tests/affected_browser.py y una consulta de solo lectura a los proveedores meteorológicos reales. No amplía la comprobación a otros flujos. Las pruebas de interfaz usan cuenta y previsión simuladas; el sondeo real se informa por separado en los logs como REAL_FORECAST. La instalación nativa y el tacto en un Android físico siguen requiriendo comprobación en dispositivo.


## 0.5.0 · Días de previsión y aventura completa

La previsión solicita hasta siete días horarios a cada proveedor. El selector recorre únicamente las fechas devueltas, con límites, Hoy y hora explícita en Europe/Madrid. Una sola respuesta por punto mantiene unidos día/hora/campos. Los datos ausentes no se sustituyen con los de otro día, y las horas pasadas no se presentan como actuales. Cambios rápidos usan una generación de render; nuevas consultas abortan e invalidan la anterior. Errores y reintento conservan el punto.

Windy usa la inserción oficial https://embed.windy.com/embed.html, con coordenadas, marcador y controles del iframe. Se mantiene su propio selector temporal, identificado expresamente: no se usan mensajes ni parámetros temporales no documentados para aparentar sincronía. La carga tiene límite de 12 segundos, error/reintento y enlace alternativo permanente. Por la política entre orígenes, un load del iframe no permite inspeccionar su contenido interno; si un bloqueo interno no emite error, la alternativa sigue visible.

Ver aventura conserva foto → ficha completa → mapa en bloques independientes. La ficha enumera los campos guardados, campos adicionales, condiciones, estimación/tiempo real diferenciados, notas y marcadores. Acciones existentes por ID, sin identificar por nombre. En móvil la barra de acciones se mantiene dentro de los límites de la ficha y no cubre la imagen ni el mapa. Si no hay imagen se omite; si la geometría no es válida la ficha permanece y se avisa junto al mapa. El borrado/restauración de una ficha con geometría dañada permite únicamente el cambio lógico de estado conservando exactamente sus datos.

Pruebas de esta entrega: solo tests/days-adventure.test.js y tests/days_adventure_browser.py, con datos/servicios simulados; sondas reales de Open-Meteo y del configurador/iframe oficiales de Windy por separado. No se modifican tablas ni datos existentes. La interacción interna real del iframe y un móvil físico se distinguen de las pruebas con iframe simulado.

## 0.6.0 · Estabilidad, ficha única y recuperación de cuenta

- Un recorrido dañado se señala y puede repararse sin bloquear el diario ni perder sus otros campos.
- Los conflictos permiten revisar campos, cargar el servidor o guardar una copia; nunca se fuerza una sobrescritura silenciosa.
- Deshacer una foto o un marcador conserva los cambios posteriores del borrador.
- Salir de la práctica limpia la consulta temporal del tiempo y restaura el estado anterior.
- «Ver aventura», los recorridos del mapa y los lugares asociados abren la misma ficha por ID.
- «He olvidado mi contraseña» solicita un enlace de Supabase y permite establecer una nueva contraseña tras validar la sesión de recuperación. Los fallos se pueden reintentar.

Las pruebas de navegador usan Chromium con cuentas, almacenamiento y correos simulados. No certifican entrega de correo, actualización de contraseña en una cuenta real ni interacción en Android físico.

La protección de contraseñas filtradas de Supabase requiere un plan Pro o superior. El proyecto utiliza Free: esta opción permanece pendiente y no se ha cambiado la facturación. Referencia: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## 0.7.0 · Viento y herramientas para salir al mar

Viento general: malla de 20 puntos de Open-Meteo, horizonte de cuatro días, actualización de consulta cada 30 minutos. Las flechas usan el punto de malla más cercano y representan el desplazamiento del viento; no son mediciones en cada cala ni una simulación del relieve local. La fecha/hora se expresa en Europe/Madrid. «Consultada» identifica la descarga, no la hora de generación del modelo. La animación se detiene al ocultar el mapa o la pestaña y respeta movimiento reducido. Las rutas siguen por encima de la capa de viento.

Fuente y condiciones: https://open-meteo.com/en/terms y https://open-meteo.com/en/docs . Uso personal no comercial, atribución Open-Meteo / CC BY 4.0. La API pública no tiene garantía de disponibilidad; las peticiones multipunto pueden computar como varias consultas. No se ha contratado ningún servicio. La comprobación de condiciones y respuesta real forma parte del proceso de publicación.

Herramientas: repetir aventuras con ID nuevo y sin datos observados ni fotos; comparación de 2–4 rutas; previsión de salida, punto medio y llegada con horas estimadas; selección de tramos pendientes; filtros combinables; resúmenes que descuentan la costa recorrida antes del periodo; zona, acceso y coordenadas diferenciadas del aparcamiento. El GPX mantiene su recorrido completo. La previsión del perfil usa ritmo uniforme y distribuye paradas, y no determina navegabilidad.

Los filtros se conservan mientras está abierta la app. Los nuevos campos son opcionales, sin migraciones. No se deduce una zona para registros antiguos. Las consultas fallidas ofrecen reintento y nunca convierten ausencias en cero. La sincronización distingue borrador local de datos guardados en cuenta.

### 0.7.1
Franja horaria comparativa en previsión completa y conservación de los filtros avanzados al entrar y salir de la práctica.

## 0.8.0 · Meteo bajo demanda

«Meteo» pide seleccionar un punto antes de abrir el bloque completo. El mapa inicial queda libre de ese bloque. Tras elegir el punto, un control inferior izquierdo muestra dirección, velocidad y rachas, brújula y manga, con evolución y una barra de horas que recorre los días disponibles. Sus datos y controles están sincronizados con la ventana detallada. Los controles no propagan gestos al trazado; cancelar o cerrar conserva el borrador y restaura la herramienta anterior. «Detalles» reabre el punto elegido; «Meteo» permite elegir uno nuevo. El viento sigue siendo una previsión de malla aproximada.

Comprobación específica: Chromium en tamaños móvil y escritorio con meteorología y cuenta simuladas; selección, cancelación, evolución, horas, ventanas y aislamiento del borrador. Pendiente de comprobación en Android físico.

## 0.8.1 · Línea temporal general permanente
Franja mínima de ancho completo en el borde inferior del mapa: dirección y velocidad en el centro del encuadre, fecha/hora, play y pausa separados y deslizador desde ahora hasta 48 horas, limitado por la disponibilidad real. Siempre visible sin seleccionar un punto ni abrir Meteo. Cambiar el punto o el día del Meteo detallado no cambia esta línea temporal general. Sin manga, rachas, explicaciones ni botones extra en el mapa.

## 0.9.0 · Regla temporal de mar

Hora fija centrada sobre una etiqueta turquesa y guía vertical. La escala inferior se desliza con días alternados y marcas horarias; arrastrar o tocar selecciona una hora disponible y pausa la reproducción. Play y pausa siguen separados. La regla conserva el horizonte de 48 horas, la independencia de Meteo y los datos existentes. El movimiento suave respeta movimiento reducido. Los tramos anteriores a la hora inicial se dibujan atenuados como contexto visual y no pueden seleccionarse.

## 0.10.0 · Oleaje azul en el mapa
Flechas azules de doble punta sobre el mar, junto a los trazos de viento. Pasivas, sin fichas ni clics, sincronizadas con la hora general del mapa. La dirección viene de Open-Meteo Marine, se convierte de procedencia a desplazamiento y se solicita con selección de celda marina. Se utiliza la costa de referencia para evitar dibujarlas sobre Menorca. Datos ausentes, fuera de hora o mar en calma no producen flechas. Un fallo marino no oculta el viento; se puede reintentar desde Meteo. La animación es visual y no representa una velocidad de propagación. Es una previsión de malla, no una medición en directo ni un cálculo de refracción local.

## 0.10.1 · Animación independiente de la hora
Pausar la evolución o elegir una hora fija detiene el reloj, pero mantiene animadas las flechas del viento y del oleaje. Las puntas ahora señalan su procedencia (de dónde vienen), coherente con las orientaciones de las fichas. La animación es orientativa y no representa desplazamiento ni velocidad física. Se siguen respetando movimiento reducido y el interruptor de animación.

## 0.11.0 · Zonas para palear

En Capas, «Zonas para palear» abre un panel bajo el mapa con fecha, hora de Menorca, duración incluyendo la vuelta y límites personales opcionales. Analiza 12 sectores amplios de la costa principal y tres puntos por sector, consultando viento, rachas, oleaje, dirección y periodo (si existe). Los máximos abarcan salida, horas intermedias y regreso, con datos de ambos proveedores alineados al mismo instante horario.

La orientación de cada punto se estima con la geometría costera y comprobaciones tierra/mar a 400, 800 y 1200 m. Si queda incierta, falta información durante la franja o la celda marina está a más de 15 km, el sector se marca con información insuficiente. Se excluyen de las propuestas los sectores con componente de viento hacia mar abierto superior a 15° respecto al paralelo de costa, cambios de dirección superiores a 45° o límites personales excedidos. Esos ángulos describen el método geométrico, no umbrales universales de seguridad.

Los candidatos restantes se ordenan por racha máxima, exposición directa al oleaje (altura por componente hacia la costa) y viento máximo, mostrando hasta tres. No hay puntuación de seguridad ni garantía de abrigo. No se modelan refracción, corrientes, protección por acantilados, restricciones o condiciones particulares de cada cala. Se muestran las limitaciones, puntos, horas, ajustes de celda y datos consultados. Las condiciones observadas pueden diferir.

«Ver zona» encuadra el sector y abre su detalle bajo el mapa. «Planificar aquí» prepara un borrador costero con ID nuevo, exige revisión y guardado, y protege cualquier borrador previo. Accesos próximos solo de lugares ya registrados; no se inventa una entrada al agua. Al mover la línea temporal o modificar la franja se retiran los resultados anteriores hasta pulsar Analizar. Caché meteorológica en memoria de 10 minutos; consultas cancelables y respuestas antiguas descartadas. Ocultar la capa retira su análisis sin borrar datos del diario. Sin migraciones de base de datos.


## 0.12.0 · Una lectura clara de la costa

Las vistas de recorridos, costa pendiente, zonas para palear y aventura seleccionada son excluyentes. Al salir se recupera la vista anterior y la selección de capas de salidas y planes. Los marcadores, bases y flechas meteorológicas mantienen sus controles propios. No se modifican datos guardados ni políticas del servidor.

En Tus recorridos, salidas de ida verdes y de ida y vuelta naranjas; planes azules discontinuos con base blanca para distinguirlos cuando coinciden. Costa pendiente se muestra sola, violeta y punteada. Dónde palear utiliza franjas semitransparentes únicamente hacia el mar, con un espacio libre sobre la línea de costa; las tarjetas y leyenda explican la exposición sin atribuir seguridad. Una aventura seleccionada aísla su recorrido con halo, nombre y tipo. Durante la edición se prioriza el borrador; al cerrar vuelve la vista previa. Ocultar o suspender una vista no elimina rutas, marcadores ni resultados del análisis. Cambiar la hora sigue invalidando resultados meteorológicos antiguos.


## 0.12.1 · Pendientes solo al solicitarlos

Las rutas pendientes azules ya no se muestran junto a las salidas en Tus recorridos. Al activar Capas → Rutas pendientes se abre una vista exclusiva con los trazados azules, sin superponer salidas ni costa pendiente. Desactivarla o pulsar Volver restaura la vista anterior y conserva la preferencia de Mis salidas. Al iniciar la aplicación las rutas pendientes permanecen ocultas. Consultar una aventura pendiente por su ID o editar su borrador sigue mostrando ese recorrido de forma aislada. La costa pendiente por recorrer también mantiene su activación explícita. Ninguna ruta o dato del diario se elimina.


## 0.12.2 · Leyenda del mapa sobre la línea temporal

Leyenda horizontal compacta sobre la hora y Play/Pausa: flechas de viento por intensidad (<15, 15–<30, ≥30 km/h), oleaje azul de doble punta, salidas verdes/naranjas, rutas pendientes azules discontinuas y costa pendiente violeta punteada. En móvil ocupa dos filas pequeñas; al activar Zonas para palear añade sus bandas de exposición (menor exposición, revisar/variable, desfavorable y sin datos). El color no clasifica seguridad. La leyenda describe los trazos y no activa capas: las rutas pendientes siguen ocultas hasta solicitarlas. Se retira la leyenda duplicada bajo el mapa y se adapta el margen inferior del encuadre a la nueva altura. Sin cambios en los datos del diario.


## 0.12.3 · Viento más visible

Flechas y leyenda de viento: verde fosforito (<15 km/h), naranja butano (15–<30 km/h) y rojo tomate (≥30 km/h). Las flechas tienen mayor opacidad y un contorno discreto para distinguirlas sobre tierra y mar. Los colores de rutas, costa pendiente, zonas y oleaje conservan su significado.
