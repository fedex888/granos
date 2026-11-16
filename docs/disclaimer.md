# Disclaimer y atribución

## Texto para la app

> Esta aplicación es una herramienta de referencia. Los precios pueden estar
> desactualizados o contener errores. No constituye asesoramiento financiero,
> comercial ni de inversión. Verificá siempre con tu corredor, acopio o
> cooperativa antes de operar.

Mostrar en:

- Onboarding (aceptación explícita).
- Detalle de producto.
- Ajustes / Acerca de.

## Atribución de fuentes

- **Cámara Arbitral de Cereales de Rosario (BCR)** — precios de pizarra.
  <https://www.cac.bcr.com.ar/es/precios-de-pizarra>
- **Ministerio de Agricultura, Ganadería y Pesca (MAGyP)** — pizarra sobre puerto.
  <https://www.magyp.gob.ar/>
- **Bolsa de Comercio de Rosario** — información de mercado.
- **Banco de la Nación Argentina (BNA)** vía **ArgentinaDatos** — cotización del
  dólar oficial. <https://argentinadatos.com/>

## Condiciones de uso

- Uso personal y gratuito en el MVP.
- No redistribuir los datos crudos con fines comerciales.
- Revisar los términos y condiciones de BCR y MAGyP antes de publicar la app.
- La app no recolecta datos personales; no hay cuentas ni login.
- FCM gestiona tokens de dispositivo; no se almacenan en el repositorio.

## Limitaciones a comunicar en la app

- No existe pizarra oficial local de Chaco: la señal se calcula sobre Rosario y el
  precio local es una **estimación** ajustable por flete.
- El precio en USD se calcula con dólar oficial de ArgentinaDatos, que puede diferir
  del dólar divisa BNA usado por BCR (≈1% al 2026-11-15).
- Los precios de girasol pueden ser estimados (`E`), no operados.
- Si el último dato tiene más de 5 días hábiles, no se generan alertas y se muestra
  un aviso de datos desactualizados.
