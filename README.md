# BCRA_bot
Bot escrito en Python para Twitter que actualiza diariamente las principales variables monetarias, publicadas por el Banco Central de la República Argentina (BCRA).

La información es extraída a las 18:30 hs. de cada día de semana (lunes a viernes) mediante pedidos a la API del Banco Central de la República Argentina ([https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp](https://www.bcra.gob.ar/BCRAyVos/catalogo-de-APIs-banco-central.asp)), que remite a las Principales Variables del mismo.

El archivo .py contiene el código en Python utilizado para los pedidos a la API y publicación (en forma de tweets) de la información diaria.

Se utilizaron productos de Google Developers, como Google Cloud Functions y Google Scheduler, para la automatización del bot.
