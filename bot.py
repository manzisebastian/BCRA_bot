def tweet_info(_context):

    # Importing
    
    import pandas as pd
    import requests
    from datetime import datetime, timedelta
    import holidays
    import tweepy
    import time
    from os import getenv

    # Obtener keys, codes y header para Estadísticas BCRA

    consumer_key = getenv("consumer_key")
    consumer_secret = getenv("consumer_secret")
    access_token = getenv("access_token")
    access_token_secret = getenv("access_token_secret")
    bearer_twitter = getenv("bearer_twitter")

    # Inicialización del Client en Tweepy y autenticación
    
    tweepy_api = tweepy.Client(
        bearer_token = bearer_twitter,
        consumer_key = consumer_key,
        consumer_secret = consumer_secret,
        access_token = access_token,
        access_token_secret = access_token_secret
        )

    # Feriados y fecha

    AR_holidays = holidays.AR()
    
    today = date.today()

    today_date = datetime.today().date()
    today_date = str(today_date)
    year_date = today_date - timedelta(days=365)
    year_date = str(year_date)

    # API del Banco Central de la República Argentina

    ## Principales variables a la fecha
    url_pv = "https://api.bcra.gob.ar/estadisticas/v1/principalesvariables"
    db_pv = requests.get(url_pv, verify=False).json()["results"]

    ids = [var["idVariable"] for var in db_pv]
    names = [var["descripcion"] for var in db_pv]

    ids_names = dict(zip(ids, names))


    ## Principales variables desde 'year_date'

    df = pd.DataFrame()
    df["fecha"] = pd.bdate_range(year_date, today_date)
    for id in ids:
        url_id = f"https://api.bcra.gob.ar/estadisticas/v1/datosvariable/{id}/{year_date}/{today_date}"
        db_id = requests.get(url_id, verify=False).json()["results"]
        df_id = pd.DataFrame(db_id)[["fecha", "valor"]]
        df_id.rename(columns = {"valor": id}, inplace=True)
        df_id[id] = df_id[id].str.replace(".", "")
        df_id[id] = df_id[id].str.replace(",", ".")
        df_id[id] = df_id[id].astype(float)
        df_id["fecha"] = pd.to_datetime(df_id["fecha"], format='%d/%m/%Y')
        df_id = df_id.sort_values('fecha').reset_index(drop=True)
        df_id = df_id[~df_id["fecha"].dt.dayofweek.isin([5, 6])].reset_index(drop=True)
        df = pd.merge(df, df_id, on="fecha", how="outer")

    last_values = []
    for id in ids:
        lv = df[id][df[id].last_valid_index()]
        last_values.append(lv)
    
    last_week_values = []
    for id in ids:
        lv = df[id][df[id].last_valid_index() - 4]
        last_week_values.append(lv)

    # Textos diarios y semanales

    text_componentes_BM = (
        "-- Componentes Base Monetaria --\n\n"
        f"La base monetaria es de ${last_values[ids.index(15)]/1000000:.3f}B.\n"
        "Composición:\n"
        f"- Circulante monetario: ${last_values[ids.index(16)]/1000000:.4f}B ({last_values[ids.index(16)]/last_values[ids.index(15)]:.2%})\n"
        f"  - Billetes y monedas en poder del público: ${last_values[ids.index(17)]/1000:.4f}B ({last_values[ids.index(17)]*1000/last_values[ids.index(16)]:.2%})\n"
        f"  - Efectivo en ent. fin.: ${last_values[ids.index(17)]:,.0f}M ({last_values[ids.index(18)]/last_values[ids.index(16)]:.2%})\n"
        f"- Depósitos en CC del BCRA: ${last_values[ids.index(17)]/1000000:.4f}B ({last_values[ids.index(19)]/last_values[ids.index(15)]:.2%})"
    )

    text_semanal_componentes_BM = (
        "-- Análisis semanal: base monetaria --\n\n"
        f"Base monetaria: {last_values[ids.index(15)]/last_week_values[ids.index(15)] - 1:{'.2%' if last_values[ids.index(15)]/last_week_values[ids.index(15)] - 1 < 0 else '+.2%'}}\n"
        f"Circulante monetario: {last_values[ids.index(16)]/last_week_values[ids.index(16)] - 1:{'.2%' if last_values[ids.index(16)]/last_week_values[ids.index(16)] - 1 < 0 else '+.2%'}}\n"
        f"Billetes y monedas: {last_values[ids.index(17)]/last_week_values[ids.index(17)] - 1:{'.2%' if last_values[ids.index(17)]/last_week_values[ids.index(17)] - 1 < 0 else '+.2%'}}\n"
        f"Efectivo en ent. fin.: {last_values[ids.index(18)]/last_week_values[ids.index(18)] - 1:{'.2%' if last_values[ids.index(18)]/last_week_values[ids.index(18)] - 1 < 0 else '+.2%'}}\n"
        f"Depósitos en CC del BCRA: {last_values[ids.index(19)]/last_week_values[ids.index(19)] - 1:{'.2%' if last_values[ids.index(19)]/last_week_values[ids.index(19)] - 1 < 0 else '+.2%'}}"
    )

    text_reservas = (
        "-- Reservas Internacionales --\n\n"
        f"Stock bruto: US${last_values[ids.index(1)]:,.0f}M.\n"
        f"Por cada US$ de Reserva, hay ${(last_values[ids.index(15)]*1000000)/(last_values[ids.index(1)]*1000000):.2f} de base monetaria y ${(last_values[ids.index(16)]*1000000)/(last_values[ids.index(1)]*1000000):.2f} de circulante monetario.\n"
        f"Variación diaria: US${last_values[ids.index(1)] - df[1][df[1].last_valid_index() - 1]:.0f}M ({last_values[ids.index(1)]/df[1][df[1].last_valid_index() - 1] - 1:{'.2%' if last_values[ids.index(1)]/df[1][df[1].last_valid_index() - 1] - 1 < 0 else '+.2%'}})"
    )

    text_semanal_reservas = (
        "-- Análisis semanal: Reservas Internacionales brutas --\n\n"
        f"Var. semanal stock Reservas: US${last_values[ids.index(1)] - last_week_values[ids.index(1)]}M ({last_values[ids.index(1)]/last_week_values[ids.index(1)] - 1:{'.2%' if last_values[ids.index(1)]/last_week_values[ids.index(1)] - 1 < 0 else '+.2%'}})\n"
        f"Stock al iniciar la semana: US${last_week_values[ids.index(1)]}M\n"
        f"Stock al terminar la semana: US${last_values[ids.index(1)]}M"
    )

    text_tc = (
        "-- Tipo de cambio --\n\n"
        f"US$ minorista: ${last_values[ids.index(4)]} por US$.\n"
        f"US$ mayorista (Com. A 3500): ${last_values[ids.index(5)]} por US$."
    )

    text_semanal_tc = (
        "-- Análisis semanal: tipo de cambio --\n\n"
        f"Var. semanal US$ minorista: ${last_values[ids.index(4)] - last_week_values[ids.index(4)]:.2f} por US$ ({last_values[ids.index(4)]/last_week_values[ids.index(4)] - 1:{'.2%' if last_values[ids.index(4)]/last_week_values[ids.index(4)] - 1 < 0 else '+.2%'}})\n"
        f"Var. semanal US$ mayorista (Com. A 3500): ${last_values[ids.index(5)] - last_week_values[ids.index(5)]:.2f} por US$ ({last_values[ids.index(5)]/last_week_values[ids.index(5)] - 1:{'.2%' if last_values[ids.index(5)]/last_week_values[ids.index(5)] - 1 < 0 else '+.2%'}})\n"
    )

    text_tasas_BCRA = (
        "-- Tasas de interés BCRA --\n\n"
        f"Tasa de política monetaria: TNA {last_values[ids.index(6)]}% - TEA {last_values[ids.index(34)]}%\n"
        "Tasas de operaciones de pase:\n"
        f"- Activa: TNA {last_values[ids.index(9)]}%\n"
        f"- Pasiva: TNA {last_values[ids.index(10)]}% - TEA {last_values[ids.index(41)]}%\n"
    )

    text_tasas_depositos = (
        "-- Tasas de interés para depósitos en ARS --\n\n"
        f"BADLAR: TNA {last_values[ids.index(10)]}% -- TEA {last_values[ids.index(35)]}%\n"
        f"BAIBAR: TNA {last_values[ids.index(11)]}%\n"
        f"Depósitos a 30d en entidades financieras: TNA {last_values[ids.index(12)]}%\n"
        f"TM20 en bancos privados (>20M ARS): TNA {last_values[ids.index(8)]}%"
    )

    text_depositos = (
        "-- Depósitos y préstamos --\n\n"
        f"Depósitos en ent. fin.: {last_values[ids.index(21)]/1000000:.4f}B.\n"
        f"- En cuentas corrientes (neto de utilización FUCO): {last_values[ids.index(22)]/1000000:.4f}B.\n"
        f"- En caja de ahorros: {last_values[ids.index(23)]/1000000:.4f}B.\n"
        f"- Plazos fijos: {last_values[ids.index(24)]/1000000:.4f}B.\n\n"
        f"Préstamos al sector privado: {last_values[ids.index(26)]/1000000:.4f}B.\n\n"
        f"Porcentaje de Préstamos en Relación a Depósitos: {last_values[ids.index(26)]/last_values[ids.index(21)]:.2%}"
    )
    
    text_semanal_depositos = (
        "-- Análisis semanal: depósitos y préstamos --\n\n"
        f"Depósitos en ent. fin.: {last_values[ids.index(21)]/last_week_values[ids.index(21)] - 1:{'.2%' if last_values[ids.index(21)]/last_week_values[ids.index(21)] - 1 < 0 else '+.2%'}}\n"
        f"- En cuentas corrientes: {last_values[ids.index(22)]/last_week_values[ids.index(22)]  - 1:{'.2%' if last_values[ids.index(22)]/last_week_values[ids.index(22)] - 1 < 0 else '+.2%'}}\n"
        f"- En caja de ahorros: {last_values[ids.index(23)]/last_week_values[ids.index(23)]  - 1:{'.2%' if last_values[ids.index(23)]/last_week_values[ids.index(23)] - 1 < 0 else '+.2%'}}\n"
        f"- Plazos fijos: {last_values[ids.index(24)]/last_week_values[ids.index(24)]  - 1:{'.2%' if last_values[ids.index(24)]/last_week_values[ids.index(24)] - 1 < 0 else '+.2%'}}\n"
        f"Préstamos al sector privado: {last_values[ids.index(26)]/last_week_values[ids.index(26)]  - 1:{'.2%' if last_values[ids.index(26)]/last_week_values[ids.index(26)] - 1 < 0 else '+.2%'}}\n"
        f"Porcentaje de Préstamos en Relación a Depósitos: {(last_values[ids.index(26)]/last_values[ids.index(21)] - last_week_values[ids.index(26)]/last_week_values[ids.index(21)])*100:{'.2f' if last_values[ids.index(26)]/last_values[ids.index(21)] - last_week_values[ids.index(26)]/last_week_values[ids.index(21)] < 0 else '+.2f'}} p.p."
    )

    text_otros_indicadores = (
        "-- Otros indicadores --\n\n"
        f"Coeficiente de Estabilización de Referencia (CER, base 2/2/2002=1): {last_values[ids.index(30)]}.\n"
        f"Unidad de Valor Adquisitivo (UVA, base 31/3/2016=14.05): {last_values[ids.index(31)]}.\n"
        f"Índice para Contratos de Locación (ICL, base 30/6/2020=1): {last_values[ids.index(40)]}."
    )

    text_feriados = (
        "¡Hoy es feriado! Las principales variables monetarias y la API del BCRA solo se actualizan los días hábiles.\n\n"
        "¡Nos vemos pronto!"
    )

    # Call a Tweepy

    if today in AR_holidays:
        tweepy_api.create_tweet(text=text_feriados)
    else:
        tweepy_api.create_tweet(text=text_componentes_BM)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][17], dayfirst=True).weekday() == 4:
            tweepy_api.create_tweet(text=text_semanal_componentes_BM)
            time.sleep(2)
        tweepy_api.create_tweet(text=text_reservas)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][0], dayfirst=True).weekday() == 4:
            tweepy_api.create_tweet(text=text_semanal_reservas)
            time.sleep(2)
        tweepy_api.create_tweet(text=text_tc)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][1], dayfirst=True).weekday() == 4:
            tweepy_api.create_tweet(text=text_semanal_tc)
            time.sleep(2)
        tweepy_api.create_tweet(text=text_tasas_BCRA)
        time.sleep(2)
        tweepy_api.create_tweet(text=text_tasas_depositos)
        time.sleep(2)
        tweepy_api.create_tweet(text=text_depositos)
        time.sleep(2)
        if pd.to_datetime(p_variables['Fecha'][23], dayfirst=True).weekday() == 4:
            tweepy_api.create_tweet(text=text_semanal_depositos)
            time.sleep(2)
        tweepy_api.create_tweet(text=text_otros_indicadores)
