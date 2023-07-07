def tweet_info(_context):

    # Importing
    
    import pandas as pd
    from bs4 import BeautifulSoup
    import requests
    import datetime
    from datetime import date
    import holidays
    from dateutil.relativedelta import relativedelta
    import tweepy
    import time
    from os import getenv

    # Obtener keys, codes y header para Estadísticas BCRA

    consumer_key = getenv("consumer_key")
    consumer_secret = getenv("consumer_secret")
    access_token = getenv("access_token")
    access_token_secret = getenv("access_token_secret")
    bearer_twitter = getenv("bearer_twitter")
    header_BCRA = getenv("header")

    header = {"Authorization": header_BCRA}
    
    # Inicialización del Client en Tweepy y autenticación
    
    tweepy_api = tweepy.Client(
        bearer_token = bearer_twitter,
        consumer_key = consumer_key,
        consumer_secret = consumer_secret,
        access_token = access_token,
        access_token_secret = access_token_secret
    )
    
    # Web scraping: principales variables del BCRA

    url_principales_variables = "http://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"

    get_request = requests.get(url_principales_variables)
    soup = BeautifulSoup(get_request.text, 'html.parser')
    tables = soup.findAll('tr')

    data = []
    for tr in tables:
    	row_data = []
    	for td in tr.findAll('td'):
        	row_data.append(td.text)
    	data.append(row_data)

    p_variables = pd.DataFrame(
    data,
    columns=['Variable', 'Fecha', 'Valor']
    )

    p_variables['Valor'] = p_variables['Valor'].str.replace('.','', regex=True)
    p_variables['Valor'] = p_variables['Valor'].str.replace(',','.', regex=True)
    p_variables['Valor'] = p_variables['Valor'].astype(float)

    p_variables = p_variables.dropna().reset_index(drop=True)

    # General: API request

    consultas = [
    "reservas",
    "usd_of",
    "usd_of_minorista",
    "base",
    "circulacion_monetaria",
    "depositos_cuenta_ent_fin",
    "billetes_y_monedas",
    "efectivo_en_ent_fin",
    "leliq",
    "depositos",
    "cuentas_corrientes",
    "cajas_ahorro",
    "plazo_fijo",
    "prestamos"
    ]

    url_general = "https://api.estadisticasbcra.com/"

    urls = []
    for consulta in consultas:
        url = url_general + consulta
        urls.append(url)

    dfs = []
    for (url, consulta) in zip(urls, consultas):
        each_df = requests.get(url, headers=header).json()
        each_df = pd.DataFrame(each_df)[-10:]
        each_df = each_df.rename(columns={'d': 'date', 'v': consulta})
        dfs.append(each_df)

    for each_df in dfs:
        each_df.set_index("date", inplace = True)

    df = pd.concat(dfs, axis=1).groupby(by="date", as_index=True)[consultas].first().reset_index()
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek
    df = df[(df['day_of_week'] != 5) & (df['day_of_week'] != 6)]
    df = df.reset_index(drop=True)
    
    # Función para extraer fecha (excluye NaN)

    def last_date(series, series_date):
    	if series.last_valid_index() is None:
        	return np.nan
    	else:
        	return series_date[series.last_valid_index()]

    # Análisis de variables: último valor

    # # Reservas Internacionales

    value_reservas = p_variables['Valor'][0]

    # # Tipo de cambio

    value_TC_min = p_variables['Valor'][1]
    value_TC_may = p_variables['Valor'][2]

    # # Tasas de interés BCRA

    value_tasa_PM_TNA = p_variables['Valor'][3]
    value_tasa_PM_TEA = p_variables['Valor'][4]
    value_tasa_REPO_activa = p_variables['Valor'][10]
    value_tasa_REPO_pasiva_TNA = p_variables['Valor'][11]
    value_tasa_REPO_pasiva_TEA = p_variables['Valor'][12]

    # # Tasas de interés por depósitos en pesos

    value_tasa_BADLAR = p_variables['Valor'][7]
    value_tasa_BAIBAR = p_variables['Valor'][13]
    value_tasa_depositos_30d = p_variables['Valor'][14]
    value_TM20 = p_variables['Valor'][9]

    # # Componentes base monetaria

    value_base = p_variables['Valor'][17]
    value_circulante = p_variables['Valor'][18]
    value_depositos_CC_en_BCRA = p_variables['Valor'][21]
    value_billetes_y_monedas = p_variables['Valor'][19]
    value_efectivo_en_entidades = p_variables['Valor'][20]
    value_M2var = p_variables['Valor'][27]

    # # LELIQs

    value_leliq = p_variables['Valor'][22]
    days_to_bm = 365/((value_tasa_PM_TEA/100*value_leliq)/value_base)

    # # Depósitos y préstamos

    value_depositos_bancos = p_variables['Valor'][23]
    value_depositos_CC = p_variables['Valor'][24]
    value_depositos_caja_ahorros = p_variables['Valor'][25]
    value_depositos_a_plazo = p_variables['Valor'][26]
    value_prestamos = p_variables['Valor'][28]

    # # Otros indicadores

    value_CER = p_variables['Valor'][33]
    value_UVA = p_variables['Valor'][34]
    value_UVI = p_variables['Valor'][35]
    value_contratos_locacion = p_variables['Valor'][36]

    # Análisis de variables: valores previos

    # # Reservas internacionales
    date_reservas_API = last_date(df[consultas[0]], df['date'])
    one_day_ago = date_reservas_API - relativedelta(days=1)
    value_reservas_day_ago = df.loc[(df['date'] - one_day_ago).abs().idxmin(), consultas[0]]
    if pd.to_datetime(p_variables['Fecha'][0], dayfirst=True).weekday() == 4:
        one_week_ago = date_reservas_API - relativedelta(weeks=4/7)
        value_reservas_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[0]]

    # # Tipo de cambio

    if pd.to_datetime(p_variables['Fecha'][1], dayfirst=True).weekday() == 4:
        date_TC_API = last_date(df[consultas[1]], df['date'])
        one_week_ago = date_TC_API - relativedelta(weeks=5/7)
        value_TC_min_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[2]]
        value_TC_may_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[1]]

    # # Componentes base monetaria

    if pd.to_datetime(p_variables['Fecha'][17], dayfirst=True).weekday() == 4:
        date_componentes_API = last_date(df[consultas[3]], df['date'])
        one_week_ago = date_componentes_API - relativedelta(weeks=4/7)
        value_base_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[3]]
        value_circulante_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[4]]
        value_depositos_CC_en_BCRA_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[5]]
        value_billetes_y_monedas_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[6]]
        value_efectivo_en_entidades_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[7]]

    # # LELIQs

    if pd.to_datetime(p_variables['Fecha'][22], dayfirst=True).weekday() == 4:
        date_leliq_API = last_date(df[consultas[8]], df['date'])
        one_week_ago = date_leliq_API - relativedelta(weeks=4/7)
        value_leliq_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[8]]

    # # Depósitos y préstamos

    if pd.to_datetime(p_variables['Fecha'][23], dayfirst=True).weekday() == 4:
        date_depositos_API = last_date(df[consultas[9]], df['date'])
        one_week_ago = date_depositos_API - relativedelta(weeks=4/7)
        value_depositos_bancos_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[9]]
        value_depositos_CC_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[10]]
        value_depositos_caja_ahorros_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[11]]
        value_depositos_a_plazo_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[12]]
        value_prestamos_week_ago = df.loc[(df['date'] - one_week_ago).abs().idxmin(), consultas[13]]

    # Textos

    text_componentes_BM = (
    "-- Componentes Base Monetaria --\n\n"
    f"La base monetaria es de ${value_base/1000000:.3f}B.\n"
    "Composición:\n"
    f"- Circulante monetario: ${value_circulante/1000000:.4f}B ({value_circulante/value_base:.2%})\n"
    f"  - Billetes y monedas en poder del público: ${value_billetes_y_monedas/1000000:.4f}B ({value_billetes_y_monedas/value_circulante:.2%})\n"
    f"  - Efectivo en ent. fin.: ${value_efectivo_en_entidades:,.0f}M ({value_efectivo_en_entidades/value_circulante:.2%})\n"
    f"- Depósitos en CC del BCRA: ${value_depositos_CC_en_BCRA/1000000:.4f}B ({value_depositos_CC_en_BCRA/value_base:.2%})"
    )

    if pd.to_datetime(p_variables['Fecha'][17], dayfirst=True).weekday() == 4:
        text_semanal_componentes_BM = (
        "-- Análisis semanal: base monetaria --\n\n"
        f"Base monetaria: {value_base/value_base_week_ago - 1:{'.2%' if value_base/value_base_week_ago - 1 < 0 else '+.2%'}}\n"
        f"Circulante monetario: {value_circulante/value_circulante_week_ago - 1:{'.2%' if value_circulante/value_circulante_week_ago - 1 < 0 else '+.2%'}}\n"
        f"Billetes y monedas: {value_billetes_y_monedas/value_billetes_y_monedas_week_ago - 1:{'.2%' if value_billetes_y_monedas/value_billetes_y_monedas_week_ago - 1 < 0 else '+.2%'}}\n"
        f"Efectivo en ent. fin.: {value_efectivo_en_entidades/value_efectivo_en_entidades_week_ago - 1:{'.2%' if value_efectivo_en_entidades/value_efectivo_en_entidades_week_ago - 1 < 0 else '+.2%'}}\n"
        f"Depósitos en CC del BCRA: {value_depositos_CC_en_BCRA/value_depositos_CC_en_BCRA_week_ago - 1:{'.2%' if value_depositos_CC_en_BCRA/value_depositos_CC_en_BCRA_week_ago - 1 < 0 else '+.2%'}}\n"
        )
  
    text_reservas = (
    "-- Reservas Internacionales --\n\n"
    f"Stock bruto: US${value_reservas:,.0f}M.\n"
    f"Por cada US$ de Reserva, hay ${(value_base*1000000)/(value_reservas*1000000):.2f} de base monetaria y ${(value_circulante*1000000)/(value_reservas*1000000):.2f} de circulante monetario.\n"
    f"Variación diaria: US${value_reservas - value_reservas_day_ago:.0f}M ({value_reservas/value_reservas_day_ago - 1:{'.2%' if value_reservas/value_reservas_day_ago - 1 < 0 else '+.2%'}})"
    )

    if pd.to_datetime(p_variables['Fecha'][0], dayfirst=True).weekday() == 4:
        text_semanal_reservas = (
        "-- Análisis semanal: Reservas Internacionales brutas --\n\n"
        f"Var. semanal stock Reservas: US${value_reservas - value_reservas_week_ago}M ({value_reservas/value_reservas_week_ago - 1:{'.2%' if value_reservas/value_reservas_week_ago - 1 < 0 else '+.2%'}})\n"
        f"Stock al iniciar la semana: US${value_reservas_week_ago}M\n"
        f"Stock al terminar la semana: US${value_reservas}M"
        )

    text_tc = (
    "-- Tipo de cambio --\n\n"
    f"US$ minorista: ${value_TC_min} por US$.\n"
    f"US$ mayorista (Com. A 3500): ${value_TC_may} por US$.\n"
    )

    if pd.to_datetime(p_variables['Fecha'][1], dayfirst=True).weekday() == 4:
        text_semanal_tc = (
        "-- Análisis semanal: tipo de cambio --\n\n"
        f"Var. semanal US$ minorista: ${value_TC_min - value_TC_min_week_ago:.2f} por US$ ({value_TC_min/value_TC_min_week_ago - 1:{'.2%' if value_TC_min/value_TC_min_week_ago - 1 < 0 else '+.2%'}})\n"
        f"Var. semanal US$ mayorista (Com. A 3500): ${value_TC_may - value_TC_may_week_ago:.2f} por US$ ({value_TC_may/value_TC_may_week_ago - 1:{'.2%' if value_TC_may/value_TC_may_week_ago - 1 < 0 else '+.2%'}})\n"
        )

    text_tasas_BCRA = (
    "-- Tasas de interés BCRA --\n\n"
    f"Tasa de política monetaria: TNA {value_tasa_PM_TNA}% - TEA {value_tasa_PM_TEA}%\n"
    "Tasas de operaciones de pase:\n"
    f"- Activa: TNA {value_tasa_REPO_activa}%\n"
    f"- Pasiva: TNA {value_tasa_REPO_pasiva_TNA}% - TEA {value_tasa_REPO_pasiva_TEA}%\n"
    )

    text_tasas_depositos = (
    "-- Tasas de interés para depósitos en ARS --\n\n"
    f"BADLAR: TNA {value_tasa_BADLAR}%\n"
    f"BAIBAR: TNA {value_tasa_BAIBAR}%\n"
    f"Depósitos a 30d en entidades financieras: TNA {value_tasa_depositos_30d}%\n"
    f"TM20 en bancos privados (>20M ARS): TNA {value_TM20}%"
    )

    text_leliq = (
    "-- Stock LELIQ --\n\n"
    f"Stock total: ${value_leliq/1000000:.4f}B.\n"
    f"Representa {value_leliq/value_base:.2f} veces el monto de la base monetaria, y juntas suman ${(value_base/1000000)+(value_leliq/1000000):.4f}B.\n"
    f"Con la tasa efectiva actual ({value_tasa_PM_TEA/100:.2%}), los intereses generan una base monetaria nueva cada {days_to_bm:.0f} días."
    )

    if pd.to_datetime(p_variables['Fecha'][22], dayfirst=True).weekday() == 4:
        text_semanal_leliq = (
        "-- Análisis semanal: Stock LELIQ --\n\n"
        f"Var. semanal stock LELIQ: ${(value_leliq - value_leliq_week_ago):,.0f}M ({value_leliq/value_leliq_week_ago - 1:{'.2%' if value_leliq/value_leliq_week_ago - 1 < 0 else '+.2%'}})\n"
        f"Stock al iniciar la semana: ${value_leliq_week_ago/1000000:.4f}B\n"
        f"Stock al terminar la semana: ${value_leliq/1000000:.4f}B"
        )

    text_depositos = (
    "-- Depósitos y préstamos --\n\n"
    f"Depósitos en ent. fin.: {value_depositos_bancos/1000000:.4f}B.\n"
    f"- En cuentas corrientes (neto de utilización FUCO): {value_depositos_CC/1000000:.4f}B.\n"
    f"- En caja de ahorros: {value_depositos_caja_ahorros/1000000:.4f}B.\n"
    f"- Plazos fijos: {value_depositos_a_plazo/1000000:.4f}B.\n\n"
    f"Préstamos al sector privado: {value_prestamos/1000000:.4f}B.\n\n"
    f"Porcentaje de Préstamos en Relación a Depósitos: {value_prestamos/value_depositos_bancos:.2%}"
    )

    if pd.to_datetime(p_variables['Fecha'][23], dayfirst=True).weekday() == 4:
        text_semanal_depositos = (
        "-- Análisis semanal: depósitos y préstamos --\n\n"
        f"Depósitos en ent. fin.: {value_depositos_bancos/value_depositos_bancos_week_ago - 1:{'.2%' if value_depositos_bancos/value_depositos_bancos_week_ago - 1 < 0 else '+.2%'}}\n"
        f"- En cuentas corrientes: {value_depositos_CC/value_depositos_CC_week_ago - 1:{'.2%' if value_depositos_CC/value_depositos_CC_week_ago - 1 < 0 else '+.2%'}}\n"
        f"- En caja de ahorros: {value_depositos_caja_ahorros/value_depositos_caja_ahorros_week_ago - 1:{'.2%' if value_depositos_caja_ahorros/value_depositos_caja_ahorros_week_ago - 1 < 0 else '+.2%'}}\n"
        f"- Plazos fijos: {value_depositos_a_plazo/value_depositos_a_plazo_week_ago - 1:{'.2%' if value_depositos_a_plazo/value_depositos_a_plazo_week_ago - 1 < 0 else '+.2%'}}\n"
        f"Préstamos al sector privado: {value_prestamos/value_prestamos_week_ago - 1:{'.2%' if value_prestamos/value_prestamos_week_ago - 1 < 0 else '+.2%'}}\n"
        f"Porcentaje de Préstamos en Relación a Depósitos: {(value_prestamos/value_depositos_bancos - value_prestamos_week_ago/value_depositos_bancos_week_ago)*100:{'.2f' if value_prestamos/value_depositos_bancos - value_prestamos_week_ago/value_depositos_bancos_week_ago < 0 else '+.2f'}} p.p."
        )

    text_otros_indicadores = (
    "-- Otros indicadores --\n\n"
    f"Coeficiente de Estabilización de Referencia (CER, base 2/2/2002=1): {value_CER}.\n"
    f"Unidad de Valor Adquisitivo (UVA, base 31/3/2016=14.05): {value_UVA}.\n"
    f"Índice para Contratos de Locación (ICL, base 30/6/2020=1): {value_contratos_locacion}."
    )

    text_feriados = (
    "¡Hoy es feriado! Las principales variables monetarias y la API del BCRA solo se actualizan los días hábiles.\n\n"
    "¡Nos vemos pronto!"
    )

    # Feriados y fecha

    AR_holidays = holidays.AR()
    
    today = date.today()

    # Call a Tweepy

    if today in AR_holidays:
        tweepy_api.update_status(status=text_feriados)
    else:
        tweepy_api.update_status(status=text_componentes_BM)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][17], dayfirst=True).weekday() == 4:
            tweepy_api.update_status(status=text_semanal_componentes_BM)
            time.sleep(2)
        tweepy_api.update_status(status=text_reservas)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][0], dayfirst=True).weekday() == 4:
            tweepy_api.update_status(status=text_semanal_reservas)
            time.sleep(2)
        tweepy_api.update_status(status=text_tc)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][1], dayfirst=True).weekday() == 4:
            tweepy_api.update_status(status=text_semanal_tc)
            time.sleep(2)
        tweepy_api.update_status(status=text_tasas_BCRA)
        time.sleep(2)
        tweepy_api.update_status(status=text_tasas_depositos)
        time.sleep(2)
        tweepy_api.update_status(status=text_leliq)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][22], dayfirst=True).weekday() == 4:
            tweepy_api.update_status(status=text_semanal_leliq)
            time.sleep(2)
        tweepy_api.update_status(status=text_depositos)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][23], dayfirst=True).weekday() == 4:
            tweepy_api.update_status(status=text_semanal_depositos)
            time.sleep(2)
        tweepy_api.update_status(status=text_otros_indicadores)
