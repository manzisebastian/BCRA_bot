# BCRA_bot
Bot escrito en Python para Twitter, que actualiza diariamente datos publicados por el Banco Central de la República Argentina (BCRA).

La información es extraída a las 19:00 hs. de cada día de semana (lunes a viernes) de la API - Estadísticas BCRA (https://estadisticasbcra.com/api/documentacion).

Estadísticas BCRA es un sitio independiente, no afiliado al BCRA ni al gobierno nacional, que compila los datos publicados diariamente por el BCRA. La información es extraída directamente desde su API.

El archivo .py contiene el código en Python utilizado para la extracción y publicación de la información diaria.

Se utilizaron productos de Google Developers, como Google Cloud Functions y Google Scheduler, para la automatización del bot.
