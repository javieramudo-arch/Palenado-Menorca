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
