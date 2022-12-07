# BCRA_bot
Bot escrito en Python para Twitter que actualiza diariamente las principales variables monetarias, publicadas por el Banco Central de la República Argentina (BCRA).

La información es extraída a las 18:30 hs. de cada día de semana (lunes a viernes) mediante un proceso de web scraping de la página oficial del Banco Central de la República Argentina (https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp).

Para los análisis semanales (y valores previos de las variables), se extrae la información de la API - Estadísticas BCRA (https://estadisticasbcra.com/api/documentacion).

Estadísticas BCRA es un sitio independiente, no afiliado al BCRA ni al gobierno nacional, que compila los datos publicados diariamente por el BCRA. La información es extraída directamente desde su API.

El archivo .py contiene el código en Python utilizado para el web scraping, request a la API y publicación (en forma de tweets) de la información diaria.

Se utilizaron productos de Google Developers, como Google Cloud Functions y Google Scheduler, para la automatización del bot.
