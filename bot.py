def tweet_info(_context):

    # Importing
    
    import pandas as pd
    import requests
    import datetime
    from dateutil.relativedelta import relativedelta
    import tweepy
    import time
    from os import getenv

    # Obtener keys, codes y header para Estadísticas BCRA

    consumer_key = getenv("consumer_key")
    consumer_secret = getenv("consumer_secret")
    access_token = getenv("access_token")
    access_token_secret = getenv("access_token_secret")
    header = getenv("header")
    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    tweepy_api = tweepy.API(auth)

    # General

    consulta = ["base", "circulacion_monetaria", "m2_privado_variacion_mensual", "leliq", "tasa_leliq", "reservas"]

    url_general = "https://api.estadisticasbcra.com/"

    def transform_df(url):
        df = requests.get(url, headers={"Authorization": header}).json()
        df = pd.DataFrame(df)
        df = df.rename(columns={'d': 'date', 'v': 'value'})
        df['date'] = pd.to_datetime(df["date"]).dt.date
        return df

    # Análisis de variables

    url_base = url_general + consulta[0]
    df_base = transform_df(url_base)
    date_base_last = df_base['date'].iloc[-1]
    value_base_last = df_base['value'].iloc[-1]

    url_circulante = url_general + consulta[1]
    df_circulante = transform_df(url_circulante)
    date_circulante_last = df_circulante['date'].iloc[-1]
    one_month_ago = date_circulante_last - relativedelta(months=1)
    value_circulante_last = df_circulante['value'].iloc[-1]
    value_circulante_month_ago = df_circulante.loc[(df_circulante['date'] - one_month_ago).abs().idxmin(), 'value']
    cond = "aumentó" if value_circulante_last/value_circulante_month_ago - 1 > 0 else "disminuyó"

    url_m2 = url_general + consulta[2]
    df_m2 = transform_df(url_m2)
    value_m2_last = df_m2['value'].iloc[-1]

    # Análisis del stock de LELIQ
    
    url_leliq = url_general + consulta[3]
    df_leliq = transform_df(url_leliq)
    date_leliq_last = df_leliq['date'].iloc[-1]
    value_leliq_last = df_leliq['value'].iloc[-1]
    leliq_year_ago = date_leliq_last - relativedelta(years=1)
    value_leliq_year_ago = df_leliq.loc[(df_leliq['date'] - leliq_year_ago).abs().idxmin(), 'value']

    url_tasa_leliq = url_general + consulta[4]
    df_tasa_leliq = transform_df(url_tasa_leliq)
    tasa_leliq_last = df_tasa_leliq['value'].iloc[-1]
    days_to_last_bm = 365/((tasa_leliq_last/100*value_leliq_last)/value_base_last)

    # Análisis de las Reservas Internacionales

    url_reservas = url_general + consulta[5]
    df_reservas = transform_df(url_reservas)
    date_reservas_last = df_reservas['date'].iloc[-1]
    value_reservas_last = df_reservas['value'].iloc[-1]
    reservas_month_ago = date_reservas_last - relativedelta(months=1)
    reservas_year_ago = date_reservas_last - relativedelta(years=1)
    value_reservas_month_ago = df_reservas.loc[(df_reservas['date'] - reservas_month_ago).abs().idxmin(), 'value']
    value_reservas_year_ago = df_reservas.loc[(df_reservas['date'] - reservas_year_ago).abs().idxmin(), 'value']
    value_reservas_prev = df_reservas['value'][len(df_reservas)-2]
    cond_2 = "aumentó" if value_reservas_last/value_reservas_prev - 1 > 0 else "disminuyó" 

    # Textos

    text_vars = (
        f"-- Principales variables monetarias al {date_base_last.strftime('%d-%m-%Y')} --\n\n"
        f"La base monetaria es de ${value_base_last/1000000:.4f}B.\n"
        f"El circulante monetario (${value_circulante_last/1000000:.4f}B) representa el {value_circulante_last/value_base_last:.2%} de la base monetaria.\n"
        f"La variación interanual del M2 privado es de {value_m2_last/100:.1%}.\n"
        f"En el último mes, el circulante monetario {cond} un {abs(value_circulante_last/value_circulante_month_ago - 1):.2%}."
    )
    text_leliq = (
        f"-- LELIQ al {date_leliq_last.strftime('%d-%m-%Y')} --\n\n"
        f"El stock total de LELIQ es de ${value_leliq_last/1000000:.4f}B.\n"
        f"Representa {value_leliq_last/value_base_last:.2f} veces el monto de la base monetaria, y juntas suman ${(value_base_last/1000000)+(value_leliq_last/1000000):.4f}B.\n"
        f"Crecimiento en el último año: {value_leliq_last/value_leliq_year_ago - 1:.2%}.\n"
        f"Con la tasa actual ({tasa_leliq_last/100:.2%}), los intereses generan una base monetaria nueva cada {days_to_last_bm:.0f} días."
    )
    text_reservas = (
        f"-- Reservas al {date_reservas_last.strftime('%d-%m-%Y')} --\n\n"
        f"El BCRA tiene US${value_reservas_last:,.0f}M como Reservas Internacionales brutas.\n"
        f"Por cada US$ de Reserva, hay ${(value_base_last*1000000)/(value_reservas_last*1000000):.2f} de base monetaria y ${(value_circulante_last*1000000)/(value_reservas_last*1000000):.2f} de circulante monetario.\n"
        f"Con respecto al dato anterior, el stock de Reservas {cond_2} en US${abs(value_reservas_last - value_reservas_prev):,.2f}M ({abs(value_reservas_last/value_reservas_prev - 1):.2%})."
    )

    # Call a Tweepy
    
    tweepy_api.update_status(status=text_vars)
    time.sleep(4)
    tweepy_api.update_status(status=text_leliq)
    time.sleep(4)
    tweepy_api.update_status(status=text_reservas)