# Trabajo en python-ecd

## Alcance

- `python-ecd` es una CLI de Typer para crear workspaces de Everybody Codes,
  descargar inputs, ejecutar soluciones y enviar respuestas.
- Mantén disponibles los dos ejecutables públicos, `ecd` y `python-ecd`.
- Las plantillas de `src/python_ecd/templates/`, incluida
  `.gitignore.tpl`, forman parte del paquete publicado. Comprueba su presencia
  cuando cambies el empaquetado o el comando `init`.

## Desarrollo

- Antes de modificar archivos, explica el cambio previsto y espera la aprobación
  del usuario.
- La aprobación para modificar no autoriza a hacer commit ni push; pide permiso
  explícito para cada operación.
- Respeta los cambios existentes aunque el árbol de trabajo no esté limpio.
- Mantén los cambios pequeños y centrados en la petición. Señala cualquier
  cambio adicional que parezca necesario antes de incluirlo en la subfase.
- Explica los resultados y las limitaciones en español, con ejemplos concretos
  cuando cambie el comportamiento visible.

## Git

- Trabaja en ramas temporales creadas desde `develop`; `main` contiene la
  versión estable.
- Usa Conventional Commits. Integra mediante pull requests con merge commit,
  sin squash ni rebase, manteniendo el título estándar del merge y el cuerpo
  vacío.
- No hagas commit, push, merge ni publiques versiones sin autorización
  explícita.
- Tras cualquier cambio ejecuta `uv run ruff format --check .`, `make lint` y
  `make test`.
- Si modificas `.github/workflows/`, valídalos con `act` cuando esté disponible
  e informa de las limitaciones de la ejecución local.
- Si cambias dependencias, actualiza `uv.lock` y ejecuta `uv lock --check`. Los
  cambios de dependencias de producción deben tratarse por separado.

## Pruebas y seguridad

- Las pruebas de la CLI deben usar `typer.testing.CliRunner` y directorios
  temporales; no deben escribir en el workspace real ni en el directorio del
  usuario.
- No accedas a Everybody Codes desde las pruebas. Sustituye `download_input` y
  `push_solution` por dobles deterministas y no uses tokens reales.
- Conserva `.env` en `.gitignore`. No muestres tokens en logs, excepciones,
  fixtures ni archivos versionados.
- Al probar `init`, `pull`, `run`, `test`, `push` o `set-token`, cubre tanto el
  resultado visible como los archivos creados o preservados en el workspace.
