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

- Todas las pull requests se integran mediante merge commit. No uses squash ni rebase.
- `main` contiene la versión estable y demostrable; `develop` integra los siguientes cambios.
- Las ramas de trabajo parten normalmente de `develop`. Los hotfix parten de `main` y sus cambios deben incorporarse después a `develop`.
- El merge commit debe mantener el título estándar `Merge pull request #...` y tener el cuerpo vacío. No repitas un título `feat:` o `fix:` en su cuerpo: Release Please lo contabilizaría además de los commits originales y duplicaría el changelog.
- Al fusionar una rama temporal, elimina la rama remota con `gh pr merge NUMERO --merge --delete-branch --subject "Merge pull request #NUMERO from propietario/rama" --body ""`.
- Tras verificar la fusión, actualiza la rama de destino y elimina la rama local temporal con `git branch -d RAMA`. No uses `git branch -D` sin autorización explícita.
- Ejecuta `git fetch --prune` para retirar referencias remotas obsoletas.
- No elimines nunca las ramas permanentes `main` o `develop`; no uses `--delete-branch` cuando cualquiera de ellas sea la rama origen de la pull request.

## Comprobaciones

- Usa `uv run` para ejecutar Python en el entorno del proyecto.
- Durante el desarrollo, ejecuta las pruebas específicas del comportamiento
  modificado.
- Al hacer commit, confía en los hooks instalados para comprobar el lock, el
  formato y el lint; no ejecutes antes `make format` y `make lint` salvo que
  necesites diagnosticar o corregir un fallo.
- Antes de una pull request, release, merge o cambio de riesgo, ejecuta la
  batería completa con `make format`, `make lint` y `make test`.
- Si no se va a crear un commit, ejecuta manualmente las comprobaciones
  relevantes antes de dar el trabajo por terminado.
- Tras modificar un workflow de GitHub Actions, si `act` está instalado, ejecuta localmente el workflow afectado y comprueba que finaliza correctamente.
- Para cambios de ejemplos, ejecuta una comprobación específica del ejemplo,
  además de las pruebas pertinentes.
- Si una comprobación no puede ejecutarse, explica cuál faltó y por qué. No
  presentes como terminada una subfase cuyas pruebas relevantes fallen.

## Releases

- Usa Conventional Commits: Release Please calcula las versiones y genera `CHANGELOG.md` a partir de ellos.
- Las versiones estables se integran mediante pull request de `develop` hacia `main`.
- Cada push a `main` ejecuta Release Please. La pull request de release se fusiona mediante merge commit con el cuerpo vacío solo cuando se quiere publicar una versión estable.
- Sigue SemVer: `fix:` incrementa el parche, `feat:` incrementa la versión menor
  y `!` o `BREAKING CHANGE:` identifican un cambio incompatible que incrementa
  la versión mayor.
- El tag `X.Y.Z` es la fuente de verdad para la versión de la aplicación; los metadatos técnicos no se sincronizan con las releases.
- No edites manualmente tags, GitHub Releases o entradas generadas del changelog salvo que la tarea solicite corregir o inicializar la automatización.
- No fusiones pull requests de release ni publiques versiones sin autorización explícita.
- Después de una release, hotfix u otro cambio exclusivo de `main`, incorpora en `develop` los cambios reales de archivos. Un merge commit adicional sin diferencias de contenido no requiere sincronización por sí solo.

## Dependencias

- No añadas dependencias de producción sin consultarlo.
- Las dependencias directas nuevas o modificadas, incluidas las de desarrollo,
  deben declarar un límite superior anterior a la siguiente versión mayor.
  Si hace falta una excepción, acuerda y documenta el motivo. Las restricciones
  existentes no se cambian fuera de una subfase de dependencias acordada.
- Cuando cambies dependencias, actualiza también `uv.lock` y comprueba que
  sigue correspondiendo a `pyproject.toml`.

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
