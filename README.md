# Paleando Menorca

Diario personal de paddle surf. Nueva edición 0.1.0, creada desde cero con HTML, CSS y JavaScript. Sin Cloudflare, sin instalación y sin compilación. El repositorio conserva por ahora el nombre técnico `Palenado-Menorca`.

## Publicación

En **Settings → Pages → Build and deployment**, seleccionar **GitHub Actions** una sola vez. El flujo `.github/workflows/pages.yml` comprobará y publicará los cambios de `main`. Si la primera ejecución se produjo antes de habilitar Pages, repetirla en **Actions → Comprobar y publicar Paleando Menorca → Run workflow**.

Dirección prevista (no implica publicación comprobada): https://javieramudo-arch.github.io/Palenado-Menorca/

## Desarrollo

Requiere Node 22+ para las pruebas y Python 3 para el servidor local.

```sh
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

Mapa Leaflet, tres bases (OpenTopoMap, PNOA, OpenStreetMap), cuatro controles independientes, GPS y radio de precisión, pantalla completa, filtros de recorridos y las cinco categorías de marcadores. Diario con búsqueda, filtro por año y favoritas, dibujo manual con puntos intermedios, edición, rutas pendientes y conversión explícita a salida. Importación GPX con revisión y exportación, distancia geodésica sin duplicar GPX, objetivos anuales, actividad mensual, lugares, fotos privadas, asociación de foto a marcador, estados de guardado y borradores por cuenta. Previsión diaria real de Open-Meteo, con errores visibles y enlace a Windy.

Práctica inicial de ocho acciones validadas: crear, marcar salida/llegada, revisar, ida y vuelta, guardar, consultar, eliminar y deshacer. Aislada del servidor y con restauración del borrador previo. No es todavía la guía de 27 pasos de la memoria original.

## Pendiente, sin datos inventados

- Geometría costera IDEIB verificada, trazado que siga esa costa, alternativa corta/larga, costa única y porcentaje pendiente. La edición actual muestra expresamente que el progreso costero no está disponible. El objetivo anual mide kilómetros paleados.
- Logo anterior de los dos palistas y la Jack Russell: no se ha recuperado; el icono actual es nuevo.
- Guía completa de 27 pasos, navegación atrás y conversión de práctica en salida real.
- Campos avanzados de accesos, condiciones recomendadas, ritmo y paradas; previsión de oleaje y comparativas entre años.
- Sincronización automática de borradores entre dispositivos. Los borradores se conservan en el navegador de la cuenta y el guardado definitivo requiere conexión.

No se incluye un service worker: los archivos se sirven por Internet para evitar actualizaciones atrapadas en cachés anteriores.

## Verificación

Pruebas unitarias reales en `tests/core.test.js`: distancias, ida y vuelta, exclusión de pendientes y eliminadas, restauración, agregación mensual, exportación y textos no confiables. Sintaxis JavaScript comprobada. La revisión de seguridad de Supabase no indicó avisos tras crear las tablas y el bucket.

La ejecución local de Chromium está bloqueada por la política del entorno. Las pruebas de navegador de CI, cuando se ejecuten, usarán backend simulado y no equivaldrán a login, fotografías, GPS o sincronización de una cuenta real. Deben comprobarse además tacto, teclado y ventanas en el Redmi Note 9 Pro, previsión real y publicación de Pages antes de considerarlas validadas.

## Servicios externos y atribución

Leaflet 1.9.4 (unpkg), supabase-js 2.57.4 (esm.sh), fuentes DM Sans/Outfit (Google Fonts), OpenStreetMap, OpenTopoMap, IGN/PNOA y Open-Meteo. La cartografía conserva su atribución. El acceso depende de conectividad y disponibilidad de esos proveedores. Los recorridos y previsiones no garantizan navegabilidad.
