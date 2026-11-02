# Auditoría de Paleando Menorca · 0.2.1

Fecha: 2 de noviembre de 2026. Base revisada: `1cc2d19d9c451dd85c53c79654e1bb648df2b066`.

## Alcance

Revisión de todos los archivos de la edición publicada: HTML, CSS, aplicación, cálculos, cliente de datos, esquema SQL, icono, documentación, pruebas y publicación de GitHub Pages. La edición publicada 0.1.0 es una aplicación distinta del ZIP anterior 3.1.2. Se conserva el modelo de datos y el proyecto Supabase actual; no se importan datos ni se sustituye el servidor por el antiguo.

## Hallazgos y correcciones

| Prioridad | Hallazgo | Cambio |
|---|---|---|
| Alta | Una escritura o carga pendiente podía aplicar su resultado a otra sesión | Comprobación de cuenta y época de sesión; invalidación de consultas, paneles, cola GPX y recuperación al cambiar de cuenta |
| Alta | La guía no comenzaba tras el login y tenía ocho acciones incompletas | Inicio tras login y carga correcta; 28 acciones, marcadores, fotografía de muestra, asociación, tiempo, menú, edición y recuperación |
| Alta | La guía no tenía retroceso ni conversión final | Puntos de restauración, atrás, salida, progreso, preferencia por cuenta en el dispositivo y conversión a borrador real revisable |
| Alta | Datos importados o manipulados podían contener fechas, trazados o valoraciones inválidos | Validación antes de guardar; protección del renderizado de valoraciones y escape de campos dinámicos |
| Media | El límite predeterminado de la API podía truncar el diario | Lectura por páginas ordenadas de 500 registros |
| Media | El borrador solo se recuperaba desde el menú | Acceso directo visible y conservación al pasar la aplicación a segundo plano |
| Media | Las fotos aparecían únicamente como nombres | Miniaturas con URL firmada, ajuste sin deformación, imagen de práctica local y errores recuperables |
| Media | El GPX dentro de una ficha no comprobaba el tamaño; un fallo dejaba una cola parcial | Límite uniforme de 10 MB y preparación completa antes de activar la cola |
| Media | Un aviso podía esconder Deshacer antes de acabar el plazo | Se mantiene accesible durante los 30 segundos; la práctica permite aprender sin límite de tiempo |
| Media | Controles del mapa no cerraban Capas y no comunicaban estado de ampliación | Cierre coherente del panel, estado accesible y salida con Escape |
| Media | Formularios estrechos y texto pequeño en móvil | Una columna, entradas de 16 px, controles táctiles, contraste, movimiento reducido y paneles adaptados |
| Media | Faltaba un dato habitual de la salida | Acceso al mar opcional, conservado al editar y visible en la ficha |
| Baja | La aplicación carecía de manifiesto | Manifiesto con rutas relativas compatibles con GitHub Pages, sin añadir caché persistente |

| Alta | La comprobación en vivo detectó HTML nuevo con JS antiguo desde caché | Referencias versionadas de CSS, aplicación y módulos para evitar mezclar versiones |

## Seguridad de Supabase comprobada en el proyecto actual

Consultas de solo lectura a catálogo y bucket, sin consultar contenido del diario:

- `public.entries` tiene RLS activa y políticas SELECT/INSERT/UPDATE/DELETE por `auth.uid() = user_id`.
- UPDATE tiene USING y WITH CHECK para impedir cambiar la propiedad de una ficha.
- `photos` es privado, limitado a 10 MB y JPEG/PNG/WebP. SELECT/INSERT/DELETE exigen la carpeta del propietario.
- El cliente incluye una clave publicable; no incluye una clave administrativa.
- El asesor de rendimiento no devuelve advertencias.
- El asesor de seguridad devuelve una advertencia: protección contra contraseñas filtradas desactivada. El conector disponible no permite cambiar esa configuración. Referencia oficial: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

No se han alterado las políticas ni el esquema y no se han eliminado archivos de fotografías.

## Pruebas y límites

`npm test`: seis grupos unitarios y un recorrido de integración de 28 acciones con DOM, cartografía y servidor simulados. Comprueba bloqueo de acciones ajenas, ruta no degenerada, práctica sin escrituras ni cargas de fotos reales, meteorología, menú, CRUD, Deshacer, retroceso, restauración exacta y rechazo de una respuesta de la cuenta anterior. La integración verifica lógica; no demuestra el comportamiento visual de un teclado Android.

GitHub Actions ejecuta además Chromium con Leaflet real y backend simulado antes de publicar. Comprueba guardar, editar, borrador, eliminar, deshacer, exclusión de rutas pendientes, aislamiento de práctica y ancho móvil. Las capturas de CI quedan en sus artefactos. La comprobación HTTPS del despliegue acredita disponibilidad del HTML/JS, no todos los servicios externos.

Pendientes que no deben presentarse como verificados: login y subida con una cuenta real; permisos GPS del dispositivo; teclado y tacto del Redmi; disponibilidad de teselas y meteo en cada conexión; correo de registro; protección de contraseñas filtradas. La costa única y el trazado automático costero siguen pendientes de geometría validada. No se inventa un porcentaje a partir de kilómetros paleados.

## Fuentes técnicas

- Código exacto de la revisión base y pruebas de este repositorio.
- Catálogo de políticas y asesores del proyecto Supabase `akjuzerljejqkizpaotw` consultados el 02/11/2026.
- Sesiones: https://supabase.com/docs/reference/javascript/auth-onauthstatechange
- Paginación: https://supabase.com/docs/reference/javascript/range
