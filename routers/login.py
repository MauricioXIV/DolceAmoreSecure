from fastapi import APIRouter, HTTPException, status, Depends, Form, Response, Request,Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Annotated, Optional
from db.client import db_client
from db.schemas.user import user_schema
from db.models.user import User, UserInDB
from passlib.context import CryptContext
from datetime import datetime, date
from bson import ObjectId

crypt = CryptContext(schemes=["bcrypt"])
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPI = 20


router = APIRouter()

templates = Jinja2Templates(directory="templates")

def search_user(field: str, key):
    user_data = db_client.users.find_one({field: key})
    if user_data is None:   
        return {"error": "User not found"}
    try:
        user = user_schema(user_data)
        return UserInDB(**user)
    except IndexError:
        return {"error": "User not found"}
    

def user_in_table(field: str, key):
    user_data = db_client.table.find_one({field: key})
    if user_data is None:
        return {"error": "Usuario no encontrado"}
    
    username = user_data.get("username")
    if username is None:
        return {"error": "No se ha encontrado el nombre de usuario"}
    
    try:
       collection = db_client["table"]
       datos = list(collection.find())
       if any(d["username"] == username for d in datos):            
            return True
       else:
           return {"error": "Credenciales inválidas"}
    except Exception as e:
        return {"error": str(e)}
    
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Credenciales inválidas")
    print(user_id)
    user = search_user("username", user_id)
    return user

lista_anidada = [
    "Galletas",
    [("Galletas grandes", 60, 1), ("Galletas medianas", 50, 1), ("Galletas chicas", 40, 1)],
    "Pasteles",
    [("Pasteles grandes", 800, 1), ("Pasteles medianos", 650, 1), ("Pasteles chicos", 400, 1)],
    [("Personalizado", 1, 1)],
    "Catálogo de Temporada",
    [("Pastel de temporada", 800, 1)],
    ("Cobro extra", 5.00, 1),
]

lista_de_compras = {}
la_suma = set()
ventas_del_dia = []
ventas_en_finanzas = []
proveedores = []
nominas = []
gastosop = []
activos = []
venta_de_activos = []
prestamos = []
dividendos = []
intereses = []
una_mas = []
caja_total = []
acreedores = []
doc_pagar = []
cred_banco = []
la_utilidad = []
prestamo_mercancia = []
hipotecota = []

def total_parcial(precio: int, cantidad: int):
    return precio * cantidad

def total_total(acumulado: int, total_parcial: int):
    return acumulado + total_parcial

def calcular_restante(precio_total: int, pagado: int) -> int:
    restante = precio_total - pagado
    return restante

def obtener_cambio(billete: int, precio: int) -> int:
    feria = billete - precio
    return feria

def obtener_siguiente_numero_de_venta():
    contador = db_client.contadores.find_one_and_update(
        {"_id": "numero_cliente"},
        {"$inc": {"secuencia": 1}},
        return_document=True,
        upsert=True
    )
    if contador is None:
        db_client.contadores.update_one(
            {"_id": "numero_cliente"},
            {"$set": {"secuencia": 1}}
        )
        contador = {"secuencia": 1}
    return contador["secuencia"]

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/finanzas", response_class=HTMLResponse)
async def dashboard_de_las_finanzas(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("dashboard_de_las_finanzas.html", {"request": request, "user": current_user.username})


@router.get("/dashboard/finanzas/fuerte", response_class=HTMLResponse)
async def dashboard_de_la_caja_fuerte(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    coleccion = db_client["caja_fuerte"]
    datos = list(coleccion.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["ultimo_corte"] = int(row["ultimo_corte"])
        row["total"] = int(row["total"])
    datos.sort(key=lambda x: x["fecha"], reverse=False)

    colection = db_client["corte_caja"]
    dutas = list(colection.find())

    for row in dutas:
        row["fecha"] = str(row["fecha"])
        row["corte_de_caja"] = int(row["corte_de_caja"])
    dutas.sort(key=lambda x: x["fecha"], reverse=False)

    return templates.TemplateResponse("caja_fuerte.html", {"request": request, "user": current_user.username, "datos": datos,
                                                           "dutas": dutas})

@router.get("/dashboard/finanzas/flujoefectivo/", response_class=HTMLResponse)
async def dashboard_de_las_finanzasas(request: Request, ventadas: int = 0, fecha: Optional[date] = Query(None, description="fecha"), current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    ventas_en_finanzas.clear()
    proveedores.clear()
    nominas.clear()
    gastosop.clear()
    activos.clear()
    venta_de_activos.clear()
    prestamos.clear()
    dividendos.clear()
    intereses.clear()

    coleccion = db_client["ventas"]
    iterador = coleccion.find()
    
    for documento in iterador:
        fecha_documento: date = documento.get("todo", {}).get("fecha")
        if str(fecha_documento) == str(fecha):
            venta_total = documento.get("todo", {}).get("total", 0)
            ventas_en_finanzas.append(venta_total)

    ventadas = sum(ventas_en_finanzas)

    collection = db_client["compras"]
    hiterador = collection.find()

    for documento in hiterador:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            compra_total = documento.get("total", 0)
            proveedores.append(compra_total)
    
    proveedoreses = sum(proveedores)

    collections = db_client["nominas"]
    hiteradors = collections.find()

    for documento in hiteradors:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            nomina_total = documento.get("total", 0)
            nominas.append(nomina_total)
    
    nominases = sum(nominas)

    collectionsus = db_client["gastos_operativos"]
    hiteradorsus = collectionsus.find()

    for documento in hiteradorsus:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            gasto_total = documento.get("total", 0)
            gastosop.append(gasto_total)
    
    gastosopus = sum(gastosop)

    impuestos = (0)

    suma_casi = proveedoreses + nominases + gastosopus + impuestos

    neto_operativas = (ventadas) - (suma_casi)

    calipto = db_client["activos"]
    el_iterador = calipto.find()

    for documento in el_iterador:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            activo_total = documento.get("total", 0)
            activos.append(activo_total)
    
    actovos = sum(activos)

    caliptoson = db_client["venta_activos"]
    el_iteradorson = caliptoson.find()

    for documento in el_iteradorson:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            venta_activo_total = documento.get("total", 0)
            venta_de_activos.append(venta_activo_total)
    
    venta_activo = sum(venta_de_activos)

    neto_inversion = (venta_activo) - (actovos)

    caliptosonson = db_client["prestamos"]
    el_iteradorsonson = caliptosonson.find()

    for documento in el_iteradorsonson:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            prestamo_total = documento.get("total", 0)
            prestamos.append(prestamo_total)
    
    presentamos = sum(prestamos)

    mexico = db_client["pagos_varios"]
    estados = mexico.find()

    for documento in estados:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            if documento.get("tipo_de_pago") == "Pago de dividendos":
                dividendo_total = documento.get("total", 0)
                dividendos.append(dividendo_total)
            if documento.get("tipo_de_pago") == "Pago de intereses":
                interes_total = documento.get("total", 0)
                intereses.append(interes_total)
    
    pago_dividendos= sum(dividendos)
    pago_intereses = sum(intereses)

    neto_financiamiento = (presentamos) - (pago_dividendos) - (pago_intereses)

    usa = db_client["capital"]
    isis = usa.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})

    capital_total = isis.get("total", 0)

    liquidez = (neto_operativas) + (neto_inversion) + (neto_financiamiento)


    return templates.TemplateResponse("flujo_de_efectivo.html", {"request": request, "user": current_user.username, "fecha": fecha,
                                                                  "ventadas": ventadas, "proveedores": proveedoreses, "nominas": nominases,
                                                                    "costos": gastosopus, "impuestos": impuestos, "neto_operativas": neto_operativas,
                                                                    "inv_activos": actovos, "venta_activos": venta_activo, "neto_inversion": neto_inversion,
                                                                    "prestamos": presentamos, "pago_dividendos": pago_dividendos, "pago_intereses": pago_intereses,
                                                                    "neto_financiamiento": neto_financiamiento, "liquidez": liquidez,
                                                                    "caja": capital_total})

@router.get("/dashboard/finanzas/flujoefectivo/json", response_class=JSONResponse)
async def obtener_liquidez(request: Request, ventadas: int = 0, fecha: Optional[date] = Query(None, description="fecha"), current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    ventas_en_finanzas.clear()
    proveedores.clear()
    nominas.clear()
    gastosop.clear()
    activos.clear()
    venta_de_activos.clear()
    prestamos.clear()
    dividendos.clear()
    intereses.clear()
    if fecha is None:
        raise HTTPException(status_code=400, detail="Fecha es requerida")

    coleccion = db_client["ventas"]
    iterador = coleccion.find()
    
    for documento in iterador:
        fecha_documento: date = documento.get("todo", {}).get("fecha")
        if str(fecha_documento) == str(fecha):
            venta_total = documento.get("todo", {}).get("total", 0)
            print(venta_total)
            ventas_en_finanzas.append(venta_total)

    ventadas = sum(ventas_en_finanzas)
    collection = db_client["compras"]
    hiterador = collection.find()

    for documento in hiterador:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            compra_total = documento.get("total", 0)
            proveedores.append(compra_total)
    
    proveedoreses = sum(proveedores)

    collections = db_client["nominas"]
    hiteradors = collections.find()

    for documento in hiteradors:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            nomina_total = documento.get("total", 0)
            nominas.append(nomina_total)
    
    nominases = sum(nominas)

    collectionsus = db_client["gastos_operativos"]
    hiteradorsus = collectionsus.find()

    for documento in hiteradorsus:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            gasto_total = documento.get("total", 0)
            gastosop.append(gasto_total)
    
    gastosopus = sum(gastosop)

    impuestos = (0)

    suma_casi = proveedoreses + nominases + gastosopus + impuestos

    neto_operativas = (ventadas) - (suma_casi)

    calipto = db_client["activos"]
    el_iterador = calipto.find()

    for documento in el_iterador:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            activo_total = documento.get("total", 0)
            activos.append(activo_total)
    
    actovos = sum(activos)

    caliptoson = db_client["venta_activos"]
    el_iteradorson = caliptoson.find()

    for documento in el_iteradorson:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            venta_activo_total = documento.get("total", 0)
            venta_de_activos.append(venta_activo_total)
    
    venta_activo = sum(venta_de_activos)

    neto_inversion = (venta_activo) - (actovos)

    caliptosonson = db_client["prestamos"]
    el_iteradorsonson = caliptosonson.find()

    for documento in el_iteradorsonson:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            prestamo_total = documento.get("total", 0)
            prestamos.append(prestamo_total)
    
    presentamos = sum(prestamos)

    mexico = db_client["pagos_varios"]
    estados = mexico.find()

    for documento in estados:
        fecha_documento: date = documento.get("fecha")
        if str(fecha_documento) == str(fecha):
            if documento.get("tipo_de_pago") == "Pago de dividendos":
                dividendo_total = documento.get("total", 0)
                dividendos.append(dividendo_total)
            if documento.get("tipo_de_pago") == "Pago de intereses":
                interes_total = documento.get("total", 0)
                intereses.append(interes_total)
    
    pago_dividendos= sum(dividendos)
    pago_intereses = sum(intereses)

    neto_financiamiento = (presentamos) - (pago_dividendos) - (pago_intereses)

    usa = db_client["capital"]
    isis = usa.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})

    capital_total = isis.get("total", 0)

    liquidez = (neto_operativas) + (neto_inversion) + (neto_financiamiento) + (capital_total)
    return {"capital_total": capital_total, "fecha": fecha}

@router.get("/dashboard/finanzas/edoderesultados", response_class=HTMLResponse)
async def dashboard_de_los_estados_de_resultados(request: Request, ventadas: int = 0, mes: Optional[str] = Query(None, description="mes"), current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    ventas_en_finanzas.clear()
    proveedores.clear()
    nominas.clear()
    gastosop.clear()
    activos.clear()
    venta_de_activos.clear()
    prestamos.clear()
    dividendos.clear()
    intereses.clear()

    coleccion = db_client["ventas"]
    iterador = coleccion.find()
    
    for documento in iterador:
        fecha_documento: date = documento.get("todo", {}).get("fecha")
        if str(mes) in str(fecha_documento):
            venta_total = documento.get("todo", {}).get("total", 0)
            ventas_en_finanzas.append(venta_total)

    ventadas = sum(ventas_en_finanzas)

    collection = db_client["compras"]
    hiterador = collection.find()

    for documento in hiterador:
        fecha_documento: date = documento.get("fecha")
        if str(mes) in str(fecha_documento):
            compra_total = documento.get("total", 0)
            proveedores.append(compra_total)
    
    proveedoreses = sum(proveedores)

    ut_bruta = (ventadas) - (proveedoreses)

    collectionsus = db_client["gastos_operativos"]
    hiteradorsus = collectionsus.find()

    for documento in hiteradorsus:
        fecha_documento: date = documento.get("fecha")
        if str(mes) in str(fecha_documento):
            gasto_total = documento.get("total", 0)
            gastosop.append(gasto_total)
    
    gastosopus = sum(gastosop)

    collections = db_client["nominas"]
    hiteradors = collections.find()

    for documento in hiteradors:
        fecha_documento: date = documento.get("fecha")
        if str(mes) in str(fecha_documento):
            nomina_total = documento.get("total", 0)
            nominas.append(nomina_total)
    
    nominases = sum(nominas)

    costos_operacion = (gastosopus) + (nominases)
    ut_operacion = (ut_bruta) - (costos_operacion)

    caliptoson = db_client["venta_activos"]
    el_iteradorson = caliptoson.find()

    for documento in el_iteradorson:
        fecha_documento: date = documento.get("fecha")
        if str(mes) in str(fecha_documento):
            venta_activo_total = documento.get("total", 0)
            venta_de_activos.append(venta_activo_total)
    
    venta_activo = sum(venta_de_activos)

    mexico = db_client["pagos_varios"]
    estados = mexico.find()

    for documento in estados:
        fecha_documento: date = documento.get("fecha")
        if str(mes) in str(fecha_documento):
            if documento.get("tipo_de_pago") == "Pago de dividendos":
                dividendo_total = documento.get("total", 0)
                dividendos.append(dividendo_total)
            if documento.get("tipo_de_pago") == "Pago de intereses":
                interes_total = documento.get("total", 0)
                intereses.append(interes_total)
    
    pago_dividendos= sum(dividendos)
    pago_intereses = sum(intereses)

    gtos_financieros = (pago_dividendos) + (pago_intereses)
    ut_antes_impuestos = (ut_operacion) + (venta_activo) - (gtos_financieros)
    isr = (ut_antes_impuestos) * (.3)
    ptu = (ut_antes_impuestos) * (.1)
    isr_y_ptu = (isr) + (ptu)
    ut_ejercicio = (ut_antes_impuestos) - (isr_y_ptu)

    return templates.TemplateResponse("edo_de_resultados.html", {"request": request, "user": current_user.username,"mes": mes, "ventadas": ventadas,
                                                                 "proveedores": proveedoreses, "ut_bruta": ut_bruta, "gtos_de_venta": gastosopus,
                                                                 "gtos_de_admon": nominases, "costos_operacion": costos_operacion, "ut_operacion": ut_operacion,
                                                                 "venta_activos": venta_activo, "gtos_financieros": gtos_financieros, "ut_antes_impuestos": ut_antes_impuestos,
                                                                 "isr": isr, "ptu": ptu, "isr_y_ptu": isr_y_ptu, "ut_ejercicio": ut_ejercicio})

@router.get("/dashboard/finanzas/balancegeneral", response_class=HTMLResponse)
async def dashboard_de_los_balances_generales(request: Request, year: Optional[str] = Query(None, description="mes"), current_user: User = Depends(get_current_user)):
    
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    ventas_en_finanzas.clear()
    proveedores.clear()
    nominas.clear()
    gastosop.clear()
    activos.clear()
    venta_de_activos.clear()
    prestamos.clear()
    dividendos.clear()
    intereses.clear()
    una_mas.clear()
    acreedores.clear()
    doc_pagar.clear()
    cred_banco.clear()
    la_utilidad.clear()
    prestamo_mercancia.clear()
    hipotecota.clear()

    lacoleccionde = db_client["utilidad_ejercicio"]
    documentosodo = lacoleccionde.find_one({"_id": ObjectId("67cf75da7bc1312076527ade")})

    if not documentosodo:
        raise HTTPException(status_code=404, detail="Documento no encontrado o no autorizado")
    la_utilidad_del_ejercicio = documentosodo.get("utilidad_ejercicio", 0)
    fecha_documento: date = documentosodo.get("fecha")
    if str(year) in str(fecha_documento):
        ut_ejercicio = la_utilidad_del_ejercicio
    else:
        ut_ejercicio = 0

    coleccion = db_client["capital"]
    iterador = coleccion.find()
    
    for documento in iterador:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            caja_total = documento.get("total", 0)
            ventas_en_finanzas.append(caja_total)

    caja = sum(ventas_en_finanzas)

    collection = db_client["banco"]
    hiterador = collection.find()

    for documento in hiterador:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            banco_total = documento.get("total", 0)
            proveedores.append(banco_total)
    
    banco = sum(proveedores)
    banco_con_utilidad = sum(proveedores) + (ut_ejercicio)

    collectionpu = db_client["compras"]
    hiteradorpu = collectionpu.find()

    akaka = db_client["almacen"]
    documentado = akaka.find_one({"_id": ObjectId("67cfa2cf5da5961fe45717ff")})
    valor_almacen = documentado.get("total", 0)

    for documento in hiteradorpu:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            compra_total = documento.get("total", 0)
            prestamos.append(compra_total)
     

    collectionsus = db_client["pedidos"]
    hiteradorsus = collectionsus.find()

    for documento in hiteradorsus:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            deuda_total = documento.get("total_restante", 0)
            gastosop.append(deuda_total)
    
    clientes = sum(gastosop)


    collections = db_client["activos"]
    hiteradors = collections.find()

    for documento in hiteradors:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            if documento.get("tipo_de_activo") == "Maquinaria y equipo":
                equipo_total = documento.get("total", 0)
                dividendos.append(equipo_total)
            if documento.get("tipo_de_activo") == "De transporte":
                transporte_total = documento.get("total", 0)
                intereses.append(transporte_total)
            if documento.get("tipo_de_activo") == "Bien inmueble":
                inmueble_total = documento.get("total", 0)
                una_mas.append(inmueble_total)
    
    b_inmuebles = sum(una_mas)
    m_y_e = sum(dividendos)
    transporte = sum(intereses)

    total_fijo = (b_inmuebles) + (m_y_e) + (transporte)

    caliptoson = db_client["gastos_operativos"]
    el_iteradorson = caliptoson.find()

    for documento in el_iteradorson:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            if documento.get("tipo_de_gasto") == "Gastos de instalación":
                instalacion_total = documento.get("total", 0)
                venta_de_activos.append(instalacion_total)
    
    gtos_instalacion = sum(venta_de_activos)


    lacoleccion = db_client["prestamos"]
    laiteracion = lacoleccion.find()

    for documento in laiteracion:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            if documento.get("colaborador") != "Proveedores" and documento.get("tipo_de_pago") != "Activo adquirido":
                deudota_total = documento.get("total", 0)
                acreedores.append(deudota_total)
    
    acreedoresus = sum(acreedores)

    mexicote = db_client["pagos_varios"]
    estadosus = mexicote.find()

    for documento in estadosus:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            if documento.get("tipo_de_pago") == "Pago de dividendos":
                dividendo_total = documento.get("total", 0)
                doc_pagar.append(dividendo_total)
            if documento.get("tipo_de_pago") == "Pago de intereses":
                interes_total = documento.get("total", 0)
                cred_banco.append(interes_total)

    españa = db_client["prestamos"]
    portugal = españa.find()

    for documento in portugal:
        fecha_documento: date = documento.get("fecha")
        if str(year) in str(fecha_documento):
            if documento.get("colaborador") == "Proveedores":
                dividendo_total = documento.get("total", 0)
                prestamo_mercancia.append(dividendo_total)
            if documento.get("tipo_de_pago") == "Activo adquirido":
                largo_total = documento.get("total", 0)
                hipotecota.append(largo_total)


    deuda_prov = sum(prestamo_mercancia)
    calaca = db_client["deuda_prov_almacen"]
    alamacen = db_client["almacen"]
    documento = calaca.find_one({"_id": ObjectId("67d250570ea24f87c33862bd")})
    cantidad = documento.get("cantidad", 0)
    if cantidad < deuda_prov:
        calaca.update_one(
        {"_id": ObjectId("67d250570ea24f87c33862bd")},
        {"$set": {"cantidad": deuda_prov}}
        )
        dacumento = alamacen.find_one({"_id": ObjectId("67cfa2cf5da5961fe45717ff")})
        total_parciel = dacumento.get("total", 0)
        super_cantidad = (total_parciel) + (cantidad)
        alamacen.update_one(
        {"_id": ObjectId("67cfa2cf5da5961fe45717ff")},
        {"$set": {"total": super_cantidad}}
        )
        valor_almacen = dacumento.get("total", 0)
    
    dacumento = alamacen.find_one({"_id": ObjectId("67cfa2cf5da5961fe45717ff")})
    valor_almacen = dacumento.get("total", 0)
    almacen = valor_almacen
    activo_circulante = (caja) + (banco_con_utilidad) + (almacen) + (clientes)
    total_activo = (activo_circulante) + (total_fijo) + (gtos_instalacion)
    d_por_pagar = sum(doc_pagar)
    c_bancarios = sum(cred_banco)
    p_c_p = (acreedoresus) + (deuda_prov)

    hipoteca = sum(hipotecota)
    total_pasivo = (hipoteca) + (p_c_p)
    capital_social = (total_activo) - (ut_ejercicio) - (total_pasivo)
    
    cs_y_ut_ejercicio = (capital_social) + (ut_ejercicio)
    p_y_c = (total_pasivo) + (cs_y_ut_ejercicio)

    return templates.TemplateResponse("balance_general.html", {"request": request, "user": current_user.username, "year": year,
                                                               "caja": caja, "bancos": banco, "almacen": almacen, "clientes": clientes,
                                                               "activo_circulante": activo_circulante, "b_inmuebles": b_inmuebles,
                                                               "m_y_e": m_y_e, "transporte": transporte, "total_fijo": total_fijo,
                                                               "gtos_instalacion": gtos_instalacion, "total_activo": total_activo,
                                                               "acreedores": acreedoresus, "d_por_pagar": d_por_pagar, "c_bancarios": c_bancarios,
                                                               "p_c_p": p_c_p, "hipoteca": hipoteca, "total_pasivo": total_pasivo,
                                                               "capital_social": capital_social, "ut_ejercicio": ut_ejercicio,
                                                               "cs_y_ut_ejercicio": cs_y_ut_ejercicio, "p_y_c": p_y_c, "banco_con_utilidad": banco_con_utilidad,
                                                               "deuda_prov": deuda_prov})

@router.get("/dashboard/finanzas/nominas", response_class=HTMLResponse)
async def dashboard_de_las_finanzas_nominas(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("nominas.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/finanzas/gastosop", response_class=HTMLResponse)
async def dashboard_de_las_finanzas_gastosop(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("gastosop.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/finanzas/activos", response_class=HTMLResponse)
async def dashboard_de_las_finanzas_activos(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("activos.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/finanzas/venta_de_activos", response_class=HTMLResponse)
async def dashboard_de_las_finanzas_activos_venta(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("venta_activos.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/finanzas/prestamos", response_class=HTMLResponse)
async def dashboard_de_las_finanzas_prestamos(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("prestamos.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/finanzas/dividendos", response_class=HTMLResponse)
async def dashboard_de_las_finanzas_prestamos(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("dividendos.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/finanzas/caja", response_class=HTMLResponse)
async def dashboard_de_las_finanzas_caja(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    return templates.TemplateResponse("capital.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/pedidos", response_class=HTMLResponse)
async def dashboard_pedidos(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("creacion_de_pedidos.html", {"request": request, "user": current_user.username})

@router.get("/dashboard/inventario", response_class=HTMLResponse)
async def dashboard_los_inventarios(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["inventario"]
    datos = list(collection.find())

    return templates.TemplateResponse("inventario.html", {"request": request, "user": current_user.username, "datos": datos})

@router.get("/actualizacion_de_pedidos/{pedido_id}", response_class=HTMLResponse)
async def actualiza_pedidos(request: Request, pedido_id: str, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    try:
        object_id = ObjectId(pedido_id)
        return templates.TemplateResponse("actualizar.html", {"request": request, "pedido_id": str(object_id)})
    
    except Exception as e:
        return HTMLResponse(content=str(e), status_code=400)

@router.get("/inicio/pedidos", response_class=HTMLResponse)
async def pedidos(request: Request, current_user: User = Depends(get_current_user), num: int = 0, date: str = ""):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    if not current_user:
        return templates.TemplateResponse("denegado.html", {"request": request})
    
    print(f"Usuario actual en posiciones: {current_user.username}")
    collection = db_client["pedidos"]
    datos = list(collection.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["cliente"] = str(row["cliente"])
        row["pedido"] = str(row["pedido"])
        row["cantidad"] = int(row["cantidad"])
        row["precio"] = int(row["precio"])
        row["indicaciones"] = str(row["indicaciones"])
        row["total"] = int(row["total"])
    datos.sort(key=lambda x: x["fecha"], reverse=False)

    return templates.TemplateResponse("pedidos.html", {"request": request, "user": current_user.username, "datos" : datos, "num": num, "date": date})

@router.get("/ultimos_movimientos", response_class=HTMLResponse)
async def recuperar(request: Request, current_user: User = Depends(get_current_user), limit: int = 10):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["movimientos"]
    movimientos = list(collection.find().sort("_id", -1).limit(limit))

    for row in movimientos:
        row["fecha"] = str(row["facha"])
        row["cliente"] = str(row["cambio"]["cliente"])
        row["pedido"] = str(row["cambio"]["pedido"])
        row["indicaciones"] = str(row["cambio"]["indicaciones"])
        row["total"] = int(row["cambio"]["total"])
        row["abono"] = int(row["cambio"]["abono"])
    return templates.TemplateResponse("last_movements.html", {"request": request, "user": current_user.username, "movimientos": movimientos})

@router.get("/inicio/cobro", response_class=HTMLResponse)
async def cobrar(request: Request, total: int = 0, cambio: int = 0, current_user: User = Depends(get_current_user)):
    collection = db_client["venta_en_mostrador"]
    ventas = list(collection.find())

    for row in ventas:
        row["fecha"] = str(row["fecha"])
        row["pedido"] = str(row["pedido"])
        row["cantidad"] = int(row["cantidad"])
        row["precio"] = int(row["precio"])

    return templates.TemplateResponse("cobro.html", {"request": request, "user": current_user.username, "lista": lista_anidada, "total": total, "ventas": ventas, "cambio": cambio})

@router.get("/total_ventas", response_class=HTMLResponse)
async def ventas_totalotas(request: Request, ventadas: int = 0, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["ventas"]
    ventas = list(collection.find())

    for row in ventas:
        row["fecha"] = str(row["todo"]["fecha"])
        row["pedido"] = str(row["todo"]["pedido"])
        row["cantidad"] = int(row["todo"]["cantidad"])
        row["precio"] = int(row["todo"]["precio"])
        row["total"] = int(row["todo"]["total"])
    ventas.sort(key=lambda x: x["fecha"], reverse=False)

    return templates.TemplateResponse("total_ventas.html", {"request": request, "user": current_user.username, "ventas": ventas, "ventadas": ventadas})

@router.get("/primeras_ventas", response_class=HTMLResponse)
async def dashboard_primeras_ventas(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["ventas"]
    ventas = list(collection.find())

    for row in ventas:
        row["fecha"] = str(row["todo"]["fecha"])
        row["pedido"] = str(row["todo"]["pedido"])
        row["cantidad"] = int(row["todo"]["cantidad"])
        row["precio"] = int(row["todo"]["precio"])
    ventas.sort(key=lambda x: x["fecha"], reverse=True)

    return templates.TemplateResponse("total_ventas.html", {"request": request, "user": current_user.username, "ventas": ventas})

@router.get("/checkout", response_class=HTMLResponse)
async def mapa_de_gears(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return templates.TemplateResponse("compras.html", {"request": request, "user": current_user.username})

@router.get("/corte_edoresultados", response_class=HTMLResponse)
async def corte_de_edo_resultados(request: Request, ut_ejercicio: Optional[int] = Query(None, description="utilidad"), current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    focha = datetime.now()
    crusi = db_client["utilidad_ejercicio"]
    viejos_datos = crusi.find_one({"_id": ObjectId("67cf75da7bc1312076527ade")})
    cantidad_anciana = viejos_datos.get("utilidad_ejercicio", 0)

    if cantidad_anciana == ut_ejercicio:
        raise HTTPException(status_code=404, detail="No hay cambios desde el último corte de ejercicio")
    if ut_ejercicio == 0:
        raise HTTPException(status_code=404, detail="Ingresa un mes específico")
    
    try:
        utilidad_ejercicio = {"fecha": focha, "utilidad_ejercicio": ut_ejercicio }
        crusi.find_one_and_replace({"_id": ObjectId("67cf75da7bc1312076527ade")}, utilidad_ejercicio)

    except Exception as e:
        return {"errorsazo": str(e)}
    
    return RedirectResponse("/dashboard/finanzas/edoderesultados", status_code=302)

@router.get("/corte_caja", response_class=HTMLResponse)
async def corte_de_caja(request: Request, caja: Optional[int] = Query(None, description="utilidad"), current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    fecha = date.today().strftime("%Y-%m-%d")
    focha = datetime.now()
    crusi = db_client["capital"]
    viejos_datos = crusi.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
    cantidad_anciana = viejos_datos.get("total", 0)
    if cantidad_anciana < 4000:
        raise HTTPException(status_code=404, detail="No la cagues, no tienes 4000 en caja")

    coleption = db_client["corte_caja"]
    corte_de_caja_dict = {"fecha": focha, "corte_de_caja": caja}
    try:
        coleption.insert_one(corte_de_caja_dict)
        crusi.update_one(
        {"_id": ObjectId("67c8a0921e6d92973db9307c")},
        {"$set": {"ultimo_corte": focha,}}
        )
        cantidad_vieja = viejos_datos.get("total", 0)
        nueva_cantidad = (cantidad_vieja) - (caja)
        crusi.update_one(
        {"_id": ObjectId("67c8a0921e6d92973db9307c")},
        {"$set": {"total": nueva_cantidad}}
        )
        hola = db_client.caja_fuerte.find_one({"_id": ObjectId("67c9df85d9a7614d7993da52")})
        el_viejo_total = hola.get("total", 0)
        el_nuevo_total = (el_viejo_total) + (caja)
        corte_dict = {"fecha": focha, "ultimo_corte": caja, "total": el_nuevo_total }
        db_client.caja_fuerte.find_one_and_replace({"_id": ObjectId("67c9df85d9a7614d7993da52")}, corte_dict)
        egresos_cap_dict = {"fecha": fecha, "pedido": "transferencia_a_caja_fuerte", "notas": None, "total": caja, "tipo_de_egreso": "Caja"}
        db_client.egresos_capital.insert_one(egresos_cap_dict)

    except Exception as e:
        return {"errorsazo": str(e)}
    
    return RedirectResponse("/dashboard/finanzas/flujoefectivo", status_code=302)

@router.get("/historia_de_las_compras", response_class=HTMLResponse)
async def la_historia_de_mis_compras(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    prestamos.clear()

    collection = db_client["compras"]
    datos = list(collection.find())

    akaka = db_client["almacen"]
    documento = akaka.find_one({"_id": ObjectId("67cfa2cf5da5961fe45717ff")})
    totalote = documento.get("total", 0)

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["proveedor"] = str(row["proveedor"])
        row["pedido"] = str(row["pedido"])
        row["cantidad"] = int(row["cantidad"])
        row["costo"] = int(row["costo"])
        row["notas"] = str(row["notas"])
        row["total"] = int(row["total"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)

    return templates.TemplateResponse("historial_de_compras.html", {"request": request, "user": current_user.username, "datos": datos,
                                                                    "totalote": totalote})

@router.get("/historia_de_las_nominas", response_class=HTMLResponse)
async def la_historia_de_mis_nominas(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["nominas"]
    datos = list(collection.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["colaborador"] = str(row["colaborador"])
        row["total"] = int(row["total"])
        row["tipo_de_pago"] = str(row["tipo_de_pago"])
        row["notas"] = str(row["notas"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)
    return templates.TemplateResponse("historial_de_nominas.html", {"request": request, "user": current_user.username, "datos": datos})

@router.get("/historia_de_los_gastos_operativos", response_class=HTMLResponse)
async def la_historia_de_mis_gastosop(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["gastos_operativos"]
    datos = list(collection.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["total"] = int(row["total"])
        row["tipo_de_gasto"] = str(row["tipo_de_gasto"])
        row["notas"] = str(row["notas"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)
    return templates.TemplateResponse("historial_de_gastosop.html", {"request": request, "user": current_user.username, "datos": datos})

@router.get("/historia_de_los_activos", response_class=HTMLResponse)
async def la_historia_de_mis_activos(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["activos"]
    datos = list(collection.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["total"] = int(row["total"])
        row["tipo_de_activo"] = str(row["tipo_de_activo"])
        row["notas"] = str(row["notas"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)
    return templates.TemplateResponse("historial_de_activos.html", {"request": request, "user": current_user.username, "datos": datos})

@router.get("/historia_de_la_venta_de_activos", response_class=HTMLResponse)
async def la_historia_de_mis_activos_vendidos(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["venta_activos"]
    datos = list(collection.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["total"] = int(row["total"])
        row["tipo_de_activo_vendido"] = str(row["tipo_de_activo_vendido"])
        row["notas"] = str(row["notas"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)
    return templates.TemplateResponse("historial_de_activos_vendidos.html", {"request": request, "user": current_user.username, "datos": datos})

@router.get("/historia_de_los_prestamos", response_class=HTMLResponse)
async def la_historia_de_mis_prestamos(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["prestamos"]
    datos = list(collection.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["total"] = int(row["total"])
        row["tipo_de_pago"] = str(row["tipo_de_pago"])
        row["notas"] = str(row["notas"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)
    return templates.TemplateResponse("historial_de_prestamos.html", {"request": request, "user": current_user.username, "datos": datos})

@router.get("/historia_de_los_dividendos", response_class=HTMLResponse)
async def la_historia_de_mis_dividendos(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["pagos_varios"]
    datos = list(collection.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["total"] = int(row["total"])
        row["tipo_de_pago"] = str(row["tipo_de_pago"])
        row["notas"] = str(row["notas"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)
    return templates.TemplateResponse("historial_de_dividendos.html", {"request": request, "user": current_user.username, "datos": datos})

@router.get("/actualiza_la_inyeccion", response_class=HTMLResponse)
async def actualiza_inyecciones(request: Request, id: Optional[str] = Query(None, description="id"), current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    return templates.TemplateResponse("actualizacion_de_inyecciones.html", {"request": request, "user": current_user.username, "id": id})

@router.get("/edita_el_almacen", response_class=HTMLResponse)
async def actualiza_almacen(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    return templates.TemplateResponse("actualizacion_de_almacen.html", {"request": request, "user": current_user.username, "id": id})

@router.get("/historia_de_las_inyecciones", response_class=HTMLResponse)
async def la_historia_de_mis_inyecciones(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["capital"]
    datos = list(collection.find())

    colection = db_client["banco"]
    dotas = list(colection.find())

    la_colection = db_client["egresos_capital"]
    dutas = list(la_colection.find())

    el_colection = db_client["egresos_banco"]
    ditas = list(el_colection.find())

    el_mato = db_client["ingresos_capital"]
    mato = list(el_mato.find())

    el_mata = db_client["ingresos_banco"]
    mata = list(el_mata.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["total"] = int(row["total"])
        row["tipo_de_pago"] = str(row["tipo_de_pago"])
        row["notas"] = str(row["notas"])
        row["ingresado_por"] = str(row["ingresado_por"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)

    for row in dotas:
        row["fecha"] = str(row["fecha"])
        row["total"] = int(row["total"])
        row["tipo_de_pago"] = str(row["tipo_de_pago"])
        row["notas"] = str(row["notas"])
        row["ingresado_por"] = str(row["ingresado_por"])
    dotas.sort(key=lambda x: x["fecha"], reverse=True)

    for row in dutas:
        row["fecha"] = str(row["fecha"])
        row["pedido"] = str(row["pedido"])
        row["total"] = int(row["total"])
        row["tipo_de_egreso"] = str(row["tipo_de_egreso"])
    dutas.sort(key=lambda x: x["fecha"], reverse=True)

    for row in ditas:
        row["fecha"] = str(row["fecha"])
        row["pedido"] = str(row["pedido"])
        row["total"] = int(row["total"])
        row["tipo_de_egreso"] = str(row["tipo_de_egreso"])
    ditas.sort(key=lambda x: x["fecha"], reverse=True)

    for row in mato:
        row["fecha"] = str(row["fecha"])
        row["pedido"] = str(row["pedido"])
        row["total"] = int(row["total"])
        row["tipo_de_ingreso"] = str(row["tipo_de_ingreso"])
    mato.sort(key=lambda x: x["fecha"], reverse=True)

    for row in mata:
        row["fecha"] = str(row["fecha"])
        row["pedido"] = str(row["pedido"])
        row["total"] = int(row["total"])
        row["tipo_de_ingreso"] = str(row["tipo_de_ingreso"])
    mata.sort(key=lambda x: x["fecha"], reverse=True)

    return templates.TemplateResponse("historial_de_inyecciones.html", {"request": request, "user": current_user.username, "datos": datos,
                                                                        "dotas": dotas, "dutas": dutas, "ditas": ditas, "mato": mato,
                                                                        "mata": mata})

@router.get("/productos_creados", response_class=HTMLResponse)
async def los_productos_que_añadiste(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    collection = db_client["añadiduras"]
    datos = list(collection.find())

    for row in datos:
        row["fecha"] = str(row["fecha"])
        row["producto"] = str(row["producto"])
        row["cantidad"] = int(row["cantidad"])
    datos.sort(key=lambda x: x["fecha"], reverse=True)
    return templates.TemplateResponse("añadiduras_realizadas.html", {"request": request, "user": current_user.username, "datos": datos})

@router.get("/abona_el_prestamo/{prestamo_id}", response_class=HTMLResponse)
async def los_prestamos_a_abonar(request: Request, prestamo_id: str, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()

    mexico = db_client["prestamos"]
    try:
        object_id = ObjectId(prestamo_id)
        prestamo = mexico.find_one({"_id": object_id})
        return templates.TemplateResponse("abono_prestamo.html", {"request": request, "prestamo_id": str(object_id), "prestamo": prestamo})
    
    except Exception as e:
        return HTMLResponse(content=str(e), status_code=400)

@router.post("/users/login")
async def login(response: Response, request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()]):
    user = search_user("username", username)
    collection = db_client["users"]
    usuario = list(collection.find({"username": username}))

    if not usuario:
        return templates.TemplateResponse("denegado.html", {"request": request})
    
    if user_in_table("username", username) is True:
        if not crypt.verify(password, user.password):
            return templates.TemplateResponse("denegado.html", {"request": request})
        
        request.session['user_id'] = user.username
        return RedirectResponse("/dashboard", status_code=302)
  
    if user and isinstance(user, UserInDB):
        if not crypt.verify(password, user.password):           
            return templates.TemplateResponse("denegado.html", {"request": request})
        
        request.session['user_id'] = user.username
        return RedirectResponse("/dashboard", status_code=302)

@router.post("/logout")
async def logout(request: Request):
    collection = db_client["cobros"]
    collection.delete_many({})
    request.session.pop("user_id", None)
    return RedirectResponse("/", status_code=302)

@router.post("/dashboard/creacion_de_pedidos")
async def creacion_de_pedidos(request: Request, fecha: str = Form(...), cliente: str = Form(...), pedido: str = Form(...), cantidad: int = Form(...), precio: int = Form(...), indicaciones: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    total = total_parcial(precio, cantidad)
    try:
        user_dict = {"id": "1", "fecha": fecha, "cliente": cliente, "pedido": pedido, "cantidad": cantidad, "precio": precio, "indicaciones": indicaciones, "total": total}
        del user_dict["id"]
        db_client.pedidos.insert_one(user_dict)
        return RedirectResponse("/inicio/pedidos", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
        
@router.post("/delete")
async def delete(request: Request, id: str = Form(...), current_user: User = Depends(get_current_user)):
    collection = db_client["pedidos"]
    coleccion = db_client["movimientos"]

    result = collection.delete_one({"_id": ObjectId(id)})
    resultado = coleccion.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        if resultado.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
        return RedirectResponse("/ultimos_movimientos", status_code=302)
    
    return RedirectResponse("/inicio/pedidos", status_code=302)

@router.post("/actualizar_pedido")
async def actualizar_el_pedido(request: Request, pedido_id: str = Form(...), fecha: str = Form(...), cliente: str = Form(...), pedido: str = Form(...), cantidad: int = Form(...), indicaciones: str = Form(...), precio: int = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["pedidos"]
    object_id = ObjectId(pedido_id)
    total: int = total_parcial(precio, cantidad)

    documento = coleccion.find_one({"_id": object_id})
    
    antiguo_total = documento.get("total")
    if not antiguo_total:
        raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    antiguo_total_restante = documento.get("total_restante")
    if not antiguo_total_restante:
        pass

    diferencia = (antiguo_total) - (total)
    nuevo_total_restante = (antiguo_total_restante) - (diferencia)
    user_dict = {"id": "1", "fecha": fecha, "cliente": cliente, "pedido": pedido, "cantidad": cantidad, "indicaciones": indicaciones, "precio": precio, "total": total, "total_restante": nuevo_total_restante }
    del user_dict["id"]

    try:
        coleccion.find_one_and_replace({"_id": object_id}, user_dict)

    except Exception as e:
        return {"errorsazo": str(e)} 

    return RedirectResponse("/inicio/pedidos", status_code=302)

@router.post("/actualizar_la_inyeccion")
async def actualizar_la_inyeccion(request: Request, id: str = Form(...), fecha: str = Form(...), cliente: str = Form(...), total: int = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["capital"]
    collection = db_client["banco"]
    object_id = ObjectId(id)

    documento = coleccion.find_one({"_id": object_id})
    if documento:
        user_dict = {"fecha": fecha, "realizado_por": cliente, "tipo_de_pago": "Caja", "total": total, "notas": cliente}
        coleccion.find_one_and_replace({"_id": object_id}, user_dict)
        return RedirectResponse("/historia_de_las_inyecciones", status_code=302)
    if not documento:
        pass
    
    dacumento = collection.find_one({"_id": object_id})
    if dacumento:
        user_dict = {"fecha": fecha, "realizado_por": cliente, "tipo_de_pago": "Transferir a banco", "total": total, "notas": cliente}
        collection.find_one_and_replace({"_id": object_id}, user_dict)
        return RedirectResponse("/historia_de_las_inyecciones", status_code=302)
    if not dacumento:
        raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")

@router.post("/resta")
async def restar_pago(request: Request, num: int = Form(...), id: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    fecha = date.today().strftime("%Y-%m-%d")
    collection = db_client["pedidos"]
    documento = collection.find_one({"_id": ObjectId(id)})
    movimientos = db_client["movimientos"]
    la_colection = db_client["capital"]

    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado o no autorizado")
    
    total_restante = int(documento.get("total_restante", 0))
    if total_restante:
        restante = calcular_restante(total_restante, num)
        collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"total_restante": restante}})
        collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"abono": num}}
        )
        dacumento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
        vieja_cantidad = dacumento.get("total", 0)
        nueva_cantidad = (vieja_cantidad) + (num)
        la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": nueva_cantidad}}
        )
        dacument = collection.find_one({"_id": ObjectId(id)})
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": "abono_pedido","pago": pago, "total": num,
                     "tipo_de_ingreso": "Caja"}
        del user_dict1["id"]
        db_client.ingresos_capital.insert_one(user_dict1)
        change_document = {
            "original_id": id,
            "facha": fecha,
            "cambio": dacument,
            "ingresado_en": pago
        }
        movimientos.insert_one(change_document)
        return RedirectResponse("/inicio/pedidos", status_code=302)
        
    precio_total = int(documento.get("total", 0))
    restante = calcular_restante(precio_total, num)
    collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"total_restante": restante}})
    collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"abono": num}}
        )
    dacumento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
    vieja_cantidad = dacumento.get("total", 0)
    nueva_cantidad = (vieja_cantidad) + (num)
    la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": nueva_cantidad}}
        )
    dacument = collection.find_one({"_id": ObjectId(id)})
    user_dict1 = {"id": "1", "fecha": fecha, "pedido": "abono_pedido","pago": pago, "total": num,
                "tipo_de_ingreso": "Caja"}
    del user_dict1["id"]
    db_client.ingresos_capital.insert_one(user_dict1)
    change_document = {
            "original_id": id,
            "facha": fecha,
            "cambio": dacument
        }
    movimientos.insert_one(change_document)
    return RedirectResponse("/inicio/pedidos", status_code=302)

@router.post("/resta2")
async def restar_pago2(request: Request, num: int = Form(...), id: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    fecha = date.today().strftime("%Y-%m-%d")
    collection = db_client["pedidos"]
    documento = collection.find_one({"_id": ObjectId(id)})
    movimientos = db_client["movimientos"]
    la_colection = db_client["banco"]

    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado o no autorizado")
    
    total_restante = int(documento.get("total_restante", 0))
    if total_restante:
        restante = calcular_restante(total_restante, num)
        collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"total_restante": restante}})
        collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"abono": num}}
        )
        dacumento = la_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
        vieja_cantidad = dacumento.get("total", 0)
        nueva_cantidad = (vieja_cantidad) + (num)
        la_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": nueva_cantidad}}
        )
        dacument = collection.find_one({"_id": ObjectId(id)})
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": "abono_pedido","pago": pago, "total": num,
                     "tipo_de_ingreso": "Banco"}
        del user_dict1["id"]
        db_client.ingresos_banco.insert_one(user_dict1)
        change_document = {
            "original_id": id,
            "facha": fecha,
            "cambio": dacument,
            "ingresado_en": pago
        }
        movimientos.insert_one(change_document)
        return RedirectResponse("/inicio/pedidos", status_code=302)
        
    precio_total = int(documento.get("total", 0))
    restante = calcular_restante(precio_total, num)
    collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"total_restante": restante}})
    collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"abono": num}}
        )
    dacumento = la_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
    vieja_cantidad = dacumento.get("total", 0)
    nueva_cantidad = (vieja_cantidad) + (num)
    la_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": nueva_cantidad}}
        )
    dacument = collection.find_one({"_id": ObjectId(id)})
    user_dict1 = {"id": "1", "fecha": fecha, "pedido": "abono_pedido","pago": pago, "total": num,
                "tipo_de_ingreso": "Banco"}
    del user_dict1["id"]
    db_client.ingresos_banco.insert_one(user_dict1)
    change_document = {
            "original_id": id,
            "facha": fecha,
            "cambio": dacument
        }
    movimientos.insert_one(change_document)
    return RedirectResponse("/inicio/pedidos", status_code=302)

@router.post("/mostrar/movimientos")
async def recuerdo(request: Request, current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    return RedirectResponse("/ultimos_movimientos", status_code=302)

@router.post("/procesar_pedido")
async def procesar_pedido(producto: str = Form(...), cantidad: int = Form(...), precio: float = Form(...), id: int = Form(...), current_user: User = Depends(get_current_user)):
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})

    total = total_parcial(precio, cantidad)
    fecha = date.today().strftime("%Y-%m-%d")
    
    pedidos = db_client["cobros"]
    papaya = db_client["venta_en_mostrador"]
    iterador = papaya.find()

    aidi = ObjectId()

    dict = {"id": id, "fecha": fecha, "producto": producto, "cantidad": cantidad}
    doct = {"fecha": fecha, "pedido": producto, "cantidad": cantidad, "precio": precio, "id": aidi, "total": total}

    pedidos.insert_one(dict)
    papaya.insert_one(doct)

    for documento in iterador:
        aydi = documento["id"]
        if aydi not in lista_de_compras:
            precio = int(documento.get("precio", 0))
            cantidad = int(documento.get("cantidad", 0))
            pedido = str(documento.get("pedido"))
            valor_de_venta = precio * cantidad

            dict = {"precio": valor_de_venta, "pedido": pedido}
            lista_de_compras["venta"] = dict
        pass

    for venta in lista_de_compras.keys():
        precio = int(lista_de_compras[venta]["precio"])
        suma = precio
        la_suma.add(suma)

    total = sum(la_suma)

    return RedirectResponse(f"/inicio/cobro?total={total}", status_code=302)

@router.post("/eliminar_pedido")
async def eliminar_el_pedido(current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    la_venta_en_mostrador = db_client["venta_en_mostrador"]
    la_venta_en_mostrador.delete_many({})
    la_suma.clear()
    return RedirectResponse("/inicio/cobro", status_code=302)

@router.post("/obtener_cambio")
async def eliminar_el_pedidote(billete: int = Form(...), precio: int = Form(...), current_user: User = Depends(get_current_user)):
    collection = db_client["cobros"]
    collection.delete_many({})
    cambio = obtener_cambio(billete, precio)
    los_cambios = db_client["cambio"]
    id: int = 1
    insertar = {"id" : id, "cambio": cambio}
    los_cambios.insert_one(insertar)

    total = sum(la_suma)

    return RedirectResponse(f"/inicio/cobro?cambio={cambio}&total={total}", status_code=302)

@router.post("/historial_de_ventas")
async def historial_ventas(caja: Optional[str] = Form(None, description="Tipo de caja(opcional)"), numero_cajas: Optional[str] = Form(None, description="Número de cajas (opcional)"), monto: Optional[int] = Form(None, description="Monto de la venta en caja"), current_user: User = Depends(get_current_user)):
    coleccion = db_client["ventas"]
    papaya = db_client["venta_en_mostrador"]
    colaction = db_client["inventario"]
    la_colection = db_client["capital"]

    documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
    cantidad_anciana = documento.get("total", 0)
    la_nueva_cantidad = (cantidad_anciana) + (monto)
    la_colection.update_one(
        {"_id": ObjectId("67c8a0921e6d92973db9307c")},
        {"$set": {"total": la_nueva_cantidad}})
    fecha = date.today().strftime("%Y-%m-%d")
    user_dict1 = {"id": "1", "fecha": fecha, "pedido": "cobro_en_caja", "total": monto,
                "tipo_de_ingreso": "Caja"}
    del user_dict1["id"]
    db_client.ingresos_capital.insert_one(user_dict1)


    if numero_cajas and numero_cajas.strip():
        numero_cajas = int(numero_cajas)
    else:
        numero_cajas = None

    dacumento = colaction.find_one({"_id": ObjectId("67b62c1d3d2a4321fe7c4389")})

    documentos = list(papaya.find({}))
    for row in documentos:
         copia_de_documento = {
        "todo": row
    }
         coleccion.insert_one(copia_de_documento)
         cantidad = int(row.get("cantidad", 0))
         pedido = str(row.get("pedido"))
         cantidad_anterior = dacumento.get(pedido)
         if cantidad_anterior is None:
            continue 
         cantidad_anterior = int(cantidad_anterior)
         nueva_cantidad = cantidad_anterior - cantidad

         colaction.update_one(
        {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
        {"$set": {pedido: nueva_cantidad}}
        )
         if "Pasteles" in pedido:
            if "grandes" in pedido:
                cantidad_antaño = int(dacumento.get("Caja pastel grande"))
                new_cantidad = cantidad_antaño - cantidad
                colaction.update_one(
                {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
                {"$set": {"Caja pastel grande": new_cantidad}}
                )
            if "medianos" in pedido:
                cantidad_antaño = int(dacumento.get("Caja pastel mediana"))
                new_cantidad = cantidad_antaño - cantidad
                colaction.update_one(
                {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
                {"$set": {"Caja pastel mediana": new_cantidad}}
                )
            if "chicos" in pedido:
                cantidad_antaño = int(dacumento.get("Caja pastel chica"))
                new_cantidad = cantidad_antaño - cantidad
                colaction.update_one(
                {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
                {"$set": {"Caja pastel chica": new_cantidad}}
                )

    if caja and numero_cajas:
        cantidad_vieja = int(dacumento.get(caja))
        newsota_cantidad: int = cantidad_vieja - int(numero_cajas)
        colaction.update_one(
        {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
        {"$set": {caja: newsota_cantidad}}
        )

    collection = db_client["cobros"]
    collection.delete_many({})
    los_cambios = db_client["cambio"]
    los_cambios.delete_many({})
    papaya.delete_many({})
    la_suma.clear()
    
    return RedirectResponse("/inicio/cobro", status_code=302)

@router.post("/eliminar_compra")
async def eliminar_la_compra(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["venta_en_mostrador"]

    documento = coleccion.find_one({"_id": ObjectId(id)})
    if documento is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    pollo = str(documento.get("pedido"))
    chuleta = int(documento.get("precio"))
    papa = int(documento.get("cantidad"))

    for key, value in list(lista_de_compras.items()):
        if value["pedido"] == pollo:
            lista_de_compras.pop(key)
            break

    mero = chuleta * papa
    la_suma.remove(mero)

    result = coleccion.delete_one({"_id": ObjectId(id)})

    if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    total = sum(la_suma)
    return RedirectResponse(f"/inicio/cobro?total={total}", status_code=302)

@router.post("/eliminar_venta")
async def eliminar_la_ventadada(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["ventas"]

    venta_de_mierda = coleccion.delete_one({"_id": ObjectId(id)})

    if venta_de_mierda.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/total_ventas", status_code=302)

@router.post("/venta_del_dia")
async def obtener_venta_total(frecha: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["ventas"]
    iterador = coleccion.find()

    ventas_del_dia.clear()

    for documento in iterador:
        print(f"Procesando documento: {documento}")
        fecha_documento = documento.get("todo", {}).get("fecha")
        if fecha_documento == frecha:
            venta_total = documento.get("todo", {}).get("total", 0)
            ventas_del_dia.append(venta_total)
            print (ventas_del_dia)

    ventadas = sum(ventas_del_dia)
    return RedirectResponse(f"/total_ventas?ventadas={ventadas}", status_code=302)

@router.post("/registro_de_venta")
async def obtener_venta_totalota(request: Request, id: str = Form(...), caja: Optional[str] = Form(None, description="Tipo de caja(opcional)"), numero_cajas: Optional[str] = Form(None, description="Número de cajas (opcional)"), current_user: User = Depends(get_current_user)):
    collection = db_client["pedidos"]
    papaya = db_client["ventas"]
    calection = db_client["inventario"]

    troca = collection.find_one({"_id": ObjectId(id)})
    introducir_documento = {
        "todo": troca
    }
    papaya.insert_one(introducir_documento)
    dacumento = calection.find_one({"_id": ObjectId("67b62c1d3d2a4321fe7c4389")})

    cantidad = int(troca.get("cantidad", 0))
    elpe_dido = str(troca.get("pedido"))
    cantidad_anterior = dacumento.get(elpe_dido)
    if cantidad_anterior is None:
        result = collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
        return RedirectResponse("/inicio/pedidos", status_code=302)
    cantidad_anterior = int(cantidad_anterior)
    nueva_cantidad = cantidad_anterior - cantidad

    calection.update_one(
    {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
    {"$set": {elpe_dido: nueva_cantidad}})

    if "Pasteles" in elpe_dido:
            if "grandes" in elpe_dido:
                cantidad_antaño = int(dacumento.get("Caja pastel grande"))
                new_cantidad = cantidad_antaño - cantidad
                calection.update_one(
                {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
                {"$set": {"Caja pastel grande": new_cantidad}}
                )
            if "medianos" in elpe_dido:
                cantidad_antaño = int(dacumento.get("Caja pastel mediana"))
                new_cantidad = cantidad_antaño - cantidad
                calection.update_one(
                {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
                {"$set": {"Caja pastel mediana": new_cantidad}}
                )
            if "chicos" in elpe_dido:
                cantidad_antaño = int(dacumento.get("Caja pastel chica"))
                new_cantidad = cantidad_antaño - cantidad
                calection.update_one(
                {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
                {"$set": {"Caja pastel chica": new_cantidad}}
                )
    
    if caja and numero_cajas:
        cantidad_anciana = int(dacumento.get(caja))
        newsosota_cantidad: int = cantidad_anciana - int(numero_cajas)
        calection.update_one(
        {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
        {"$set": {caja: newsosota_cantidad}}
        )

    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    return RedirectResponse("/inicio/pedidos", status_code=302)

@router.post("/resta_manual")
async def eliminar_en_inventario(id: int = Form(...), aidi: str = Form(...), producto: str = Form(...), current_user: User = Depends(get_current_user)):
    collection = db_client["inventario"]
    nuevo_total = id - 1

    collection.update_one(
        {"_id": ObjectId(aidi)},
        {"$set": {producto: nuevo_total}}
        )
    
    return RedirectResponse("/dashboard/inventario", status_code=302)

@router.post("/suma_manual")
async def añadir_en_inventario(id: int = Form(...), aidi: str = Form(...), producto: str = Form(...), current_user: User = Depends(get_current_user)):
    collection = db_client["inventario"]
    nuevo_total = id + 1

    collection.update_one(
        {"_id": ObjectId(aidi)},
        {"$set": {producto: nuevo_total}}
        )
    
    return RedirectResponse("/dashboard/inventario", status_code=302)

@router.post("/compra_realizada")
async def creacion_de_pedidos(request: Request, fecha: str = Form(...), proveedor: str = Form(...), pedido: str = Form(...), cantidad: int = Form(...), costo: int = Form(...), notas: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    total = total_parcial(costo, cantidad)
    collection = db_client["inventario"]
    la_colection = db_client["capital"]
    el_colection = db_client["banco"]
    try:
        user_dict = {"id": "1", "fecha": fecha, "proveedor": proveedor, "pedido": pedido, "cantidad": cantidad, "costo": costo, "notas": notas,"pago": pago, "total": total}
        user_dict1 = {"id": "1", "fecha": fecha, "proveedor": proveedor, "pedido": pedido, "cantidad": cantidad, "costo": costo, "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Caja"}
        user_dict2 = {"id": "1", "fecha": fecha, "proveedor": proveedor, "pedido": pedido, "cantidad": cantidad, "costo": costo, "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Banco"}
        del user_dict["id"]
        del user_dict1["id"]
        del user_dict2["id"]
        db_client.compras.insert_one(user_dict)
        if pago == "Caja":
            documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_capital.insert_one(user_dict1)
        if pago == "Banco":
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_banco.insert_one(user_dict2)

        producto_del_inventario = pedido
        cantidad_a_sumar = cantidad
        documento = collection.find_one({"_id": ObjectId("67b62c1d3d2a4321fe7c4389")})
        cantidad_anterior = int(documento.get(pedido, 0))
        nueva_cantidad = cantidad_anterior + cantidad_a_sumar

        collection.update_one(
        {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
        {"$set": {producto_del_inventario: nueva_cantidad}}
        )

        return RedirectResponse("/historia_de_las_compras", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}

@router.post("/elimina_la_compra")
async def eliminar_la_compra_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["compras"]

    venta_de_mierda = coleccion.delete_one({"_id": ObjectId(id)})

    if venta_de_mierda.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_las_compras", status_code=302)

@router.post("/elimina_la_añadidura")
async def eliminar_la_añadidura_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["añadiduras"]

    venta_de_mierda = coleccion.delete_one({"_id": ObjectId(id)})

    if venta_de_mierda.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/productos_creados", status_code=302)

@router.post("/añade_productos")
async def creacion_de_pedidos(request: Request, fecha: str = Form(...), producto: str = Form(...), cantidad: int = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    collection = db_client["inventario"]

    try:
        user_dict = {"id": "1", "fecha": fecha, "producto": producto, "cantidad": cantidad}
        del user_dict["id"]
        db_client.añadiduras.insert_one(user_dict)
        producto_del_inventario = producto
        cantidad_a_sumar = cantidad
        documento = collection.find_one({"_id": ObjectId("67b62c1d3d2a4321fe7c4389")})
        cantidad_anterior = int(documento.get(producto, 0))
        nueva_cantidad = cantidad_anterior + cantidad_a_sumar

        collection.update_one(
        {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
        {"$set": {producto_del_inventario: nueva_cantidad}}
        )

        return RedirectResponse("/dashboard/inventario", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
    
@router.post("/resta_de_cajas_galletas")
async def resta_las_cajas_galletas(request: Request, caja: Optional[str] = Form(None, description="Tipo de caja(opcional)"), numero_cajas: Optional[str] = Form(None, description="Número de cajas (opcional)"), current_user: User = Depends(get_current_user)):
    calection = db_client["inventario"]
    dacumento = calection.find_one({"_id": ObjectId("67b62c1d3d2a4321fe7c4389")})
    
    if caja and numero_cajas:
        cantidad_anciana = int(dacumento.get(caja))
        newsosota_cantidad: int = cantidad_anciana - int(numero_cajas)
        calection.update_one(
        {"_id": ObjectId("67b62c1d3d2a4321fe7c4389")},
        {"$set": {caja: newsosota_cantidad}}
        )

    return RedirectResponse("/inicio/pedidos", status_code=302)

@router.post("/ventas_del_dia")
async def obtener_venta_total_en_finanzas(frecha: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["ventas"]
    iterador = coleccion.find()

    ventas_del_dia.clear()
    ventas_en_finanzas.clear()

    for documento in iterador:
        print(f"Procesando documento: {documento}")
        fecha_documento = documento.get("todo", {}).get("fecha")
        if fecha_documento == frecha:
            venta_total = documento.get("todo", {}).get("total", 0)
            ventas_en_finanzas.append(venta_total)
            print (ventas_en_finanzas)

    ventadas = sum(ventas_en_finanzas)
    return RedirectResponse(f"/dashboard/finanzas/flujoefectivo?ventadas={ventadas}", status_code=302)

@router.post("/nomina")
async def las_nominas(request: Request, fecha: str = Form(...), colaborador: str = Form(...), tipo_de_pago: str = Form(...), total: int = Form(...),notas: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    la_colection = db_client["capital"]
    el_colection = db_client["banco"]
    
    try:
        user_dict = {"id": "1", "fecha": fecha, "colaborador": colaborador,"tipo_de_pago": tipo_de_pago, "total": total, "notas": notas}
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": "nómina", "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Caja"}
        user_dict2 = {"id": "1", "fecha": fecha, "pedido": "nómina", "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Banco"}
        del user_dict["id"]
        del user_dict1["id"]
        del user_dict2["id"]
        db_client.nominas.insert_one(user_dict)
        if pago == "Caja":
            documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_capital.insert_one(user_dict1)
        if pago == "Banco":
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_banco.insert_one(user_dict2)

        return RedirectResponse("/historia_de_las_nominas", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
    
@router.post("/elimina_la_nomina")
async def eliminar_la_nomina_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["nominas"]

    nomina_de_mierda = coleccion.delete_one({"_id": ObjectId(id)})

    if nomina_de_mierda.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_las_nominas", status_code=302)

@router.post("/gasto_operativo")
async def los_gastos_operativos(request: Request, fecha: str = Form(...), tipo_de_gasto_operativo: str = Form(...), total: int = Form(...),notas: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    la_colection = db_client["capital"]
    el_colection = db_client["banco"]

    try:
        user_dict = {"id": "1", "fecha": fecha, "tipo_de_gasto": tipo_de_gasto_operativo, "total": total, "notas": notas}
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": tipo_de_gasto_operativo, "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Caja"}
        user_dict2 = {"id": "1", "fecha": fecha, "pedido": tipo_de_gasto_operativo, "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Banco"}
        del user_dict["id"]
        del user_dict1["id"]
        del user_dict2["id"]
        db_client.gastos_operativos.insert_one(user_dict)
        if pago == "Caja":
            documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_capital.insert_one(user_dict1)
        if pago == "Banco":
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_banco.insert_one(user_dict2)

        return RedirectResponse("/historia_de_los_gastos_operativos", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
    
@router.post("/elimina_el_gasto")
async def eliminar_el_gasto_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["gastos_operativos"]

    gasto_operativo = coleccion.delete_one({"_id": ObjectId(id)})

    if gasto_operativo.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_los_gastos_operativos", status_code=302)

@router.post("/nuevo_activo")
async def los_nuevos_activos(request: Request, fecha: str = Form(...), tipo_de_activo: str = Form(...), total: int = Form(...), notas: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    el_colection = db_client["banco"]

    try:
        user_dict = {"id": "1", "fecha": fecha, "tipo_de_activo": tipo_de_activo, "total": total, "notas": notas}
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": "prestamo_largo_plazo", "tipo_de_pago": "Activo adquirido", "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Préstamo"}
        user_dict2 = {"id": "1", "fecha": fecha, "pedido": "prestamo_largo_plazo", "tipo_de_pago": None, "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Banco"}
        del user_dict["id"]
        del user_dict1["id"]
        del user_dict2["id"]
        db_client.activos.insert_one(user_dict)

        if pago == "Préstamo":
            db_client.prestamos.insert_one(user_dict1)
        if pago == "Banco":
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_banco.insert_one(user_dict2)

        return RedirectResponse("/historia_de_los_activos", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
    
@router.post("/elimina_el_activo")
async def eliminar_el_activo_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["activos"]

    activo = coleccion.delete_one({"_id": ObjectId(id)})

    if activo.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_los_activos", status_code=302)

@router.post("/venta_de_activo")
async def los_activos_vendidos(request: Request, fecha: str = Form(...), tipo_de_activo_vendido: str = Form(...), total: int = Form(...), notas: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    la_colection = db_client["capital"]
    el_colection = db_client["banco"]
    try:
        user_dict = {"id": "1", "fecha": fecha, "tipo_de_activo_vendido": tipo_de_activo_vendido, "total": total, "notas": notas, "ingresado_en": pago}
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": tipo_de_activo_vendido, "notas": notas,"pago": pago, "total": total,
                     "tipo_de_ingreso": "Caja"}
        user_dict2 = {"id": "1", "fecha": fecha, "pedido": tipo_de_activo_vendido, "notas": notas,"pago": pago, "total": total,
                     "tipo_de_ingreso": "Banco"}
        del user_dict["id"]
        del user_dict1["id"]
        del user_dict2["id"]
        db_client.venta_activos.insert_one(user_dict)

        if pago == "Caja":
            documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) + (total)
            la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.ingresos_capital.insert_one(user_dict1)
        if pago == "Banco":
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) + (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.ingresos_banco.insert_one(user_dict2)
        return RedirectResponse("/historia_de_la_venta_de_activos", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
    
@router.post("/elimina_el_activo_vendido")
async def eliminar_la_venta_del_activo_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["venta_activos"]

    activo = coleccion.delete_one({"_id": ObjectId(id)})

    if activo.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_la_venta_de_activos", status_code=302)

@router.post("/prestamo")
async def los_prestamos(request: Request, fecha: str = Form(...), tipo_de_pago: str = Form(...), colaborador: str = Form(...), total: int = Form(...), notas: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    la_colection = db_client["capital"]
    el_colection = db_client["banco"]
    calaca = db_client["almacen"]
    try:
        user_dict = {"id": "1", "fecha": fecha, "tipo_de_pago": tipo_de_pago, "total": total, "colaborador": colaborador, "notas": notas, "ingresado_a": pago}
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": "prestamo_ingresado", "notas": notas,"pago": pago, "total": total,
                     "tipo_de_ingreso": "Caja"}
        user_dict2 = {"id": "1", "fecha": fecha, "pedido": "prestamo ingresado", "notas": notas,"pago": pago, "total": total,
                     "tipo_de_ingreso": "Banco"}
        del user_dict["id"]
        del user_dict1["id"]
        del user_dict2["id"]
        db_client.prestamos.insert_one(user_dict)

        if pago == "Caja":
            if colaborador == "Proveedores":
                documento = calaca.find_one({"_id": ObjectId("67cfa2cf5da5961fe45717ff")})
                cantidad_antaño = documento.get("total", 0)
                la_nueva_cantidad = (cantidad_antaño) + (total)
                calaca.update_one(
                {"_id": ObjectId("67cfa2cf5da5961fe45717ff")},
                {"$set": {"total": la_nueva_cantidad}}
                )
                return RedirectResponse("/historia_de_los_prestamos", status_code=302)
            documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) + (total)
            la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.ingresos_capital.insert_one(user_dict1)
        if pago == "Banco":
            if colaborador == "Proveedores":
                documento = calaca.find_one({"_id": ObjectId("67cfa2cf5da5961fe45717ff")})
                cantidad_antaño = documento.get("total", 0)
                la_nueva_cantidad = (cantidad_antaño) + (total)
                calaca.update_one(
                {"_id": ObjectId("67cfa2cf5da5961fe45717ff")},
                {"$set": {"total": la_nueva_cantidad}}
                )
                return RedirectResponse("/historia_de_los_prestamos", status_code=302)
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) + (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.ingresos_banco.insert_one(user_dict2)

        return RedirectResponse("/historia_de_los_prestamos", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
    
@router.post("/elimina_el_prestamo")
async def eliminar_el_prestamo_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["prestamos"]

    prestamo = coleccion.delete_one({"_id": ObjectId(id)})

    if prestamo.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_los_prestamos", status_code=302)

@router.post("/dividendo")
async def los_dividendos(request: Request, fecha: str = Form(...), tipo_de_pago: str = Form(...), total: int = Form(...), notas: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    la_colection = db_client["capital"]
    el_colection = db_client["banco"]
    try:
        user_dict = {"id": "1", "fecha": fecha, "tipo_de_pago": tipo_de_pago, "total": total, "notas": notas}
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": "dividendo_pagado", "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Caja"}
        user_dict2 = {"id": "1", "fecha": fecha, "pedido": "dividendo_pagado", "notas": notas,"pago": pago, "total": total,
                     "tipo_de_egreso": "Banco"}
        del user_dict["id"]
        del user_dict1["id"]
        del user_dict2["id"]
        db_client.pagos_varios.insert_one(user_dict)

        if pago == "Caja":
            documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_capital.insert_one(user_dict1)
        if pago == "Banco":
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_banco.insert_one(user_dict2)


        return RedirectResponse("/historia_de_los_dividendos", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
    
@router.post("/elimina_el_dividendo")
async def eliminar_el_pago_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["pagos_varios"]

    pago = coleccion.delete_one({"_id": ObjectId(id)})

    if pago.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_los_dividendos", status_code=302)

@router.post("/capital")
async def el_capital(request: Request, fecha: str = Form(...), colaborador: str = Form(...), tipo_de_pago: str = Form(...), total: int = Form(...), notas: str = Form(...), current_user: User = Depends(get_current_user)):
    colection = db_client["cobros"]
    colection.delete_many({})
    calasion = db_client["capital"]
    dacumento = calasion.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
    colasion = db_client["banco"]
    docusion = colasion.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
    caja_total.clear()

    try:
        if tipo_de_pago == "Caja":
            el_total = dacumento.get("total", 0)
            nuevo_total = (el_total) + (total)
            user_dict = {"fecha": fecha, "tipo_de_pago": tipo_de_pago, "ingresado_por": colaborador, "total": nuevo_total, "notas": notas}
            user_dict2 = {"id": "1", "fecha": fecha, "pedido": "inyección_a_caja", "notas": notas, "total": total,
                     "tipo_de_ingreso": "Caja"}
            del user_dict2["id"]
            db_client.capital.find_one_and_replace({"_id": ObjectId("67c8a0921e6d92973db9307c")}, user_dict)
            db_client.ingresos_capital.insert_one(user_dict2)


        if tipo_de_pago == "Transferir a banco":
            el_total = docusion.get("total", 0)
            nuevo_total = (el_total) + (total)
            user_dict = {"fecha": fecha, "tipo_de_pago": tipo_de_pago, "ingresado_por": colaborador, "total": nuevo_total, "notas": notas}
            user_dict1 = {"id": "1", "fecha": fecha, "pedido": "transferencia_desde_caja", "notas": notas, "total": total,
                     "tipo_de_egreso": "Caja"}
            user_dict2 = {"id": "1", "fecha": fecha, "pedido": "transferencia_desde_caja", "notas": notas, "total": total,
                     "tipo_de_ingreso": "Banco"}
            del user_dict2["id"]
            del user_dict1["id"]
            db_client.banco.find_one_and_replace({"_id": ObjectId("67c89fa41e6d92973db9307b")}, user_dict)
            db_client.ingresos_banco.insert_one(user_dict2)
            db_client.egresos_capital.insert_one(user_dict1)
            total_de_caja = dacumento.get("total")
            nuevo_total_de_caja = (total_de_caja) - (total)
            calasion.update_one(
        {"_id": ObjectId("67c8a0921e6d92973db9307c")},
        {"$set": {"total": nuevo_total_de_caja}}
        )
            
        return RedirectResponse("/historia_de_las_inyecciones", status_code=302)
    
    except Exception as e:
        return {"errorsazo": str(e)}
    
@router.post("/elimina_la_inyeccion")
async def eliminar_el_pago_del_historial(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["capital"]

    pago = coleccion.delete_one({"_id": ObjectId(id)})

    if pago.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_las_inyecciones", status_code=302)

@router.post("/reseteo_fuerte")
async def resetear_Caja_fuerte(current_user: User = Depends(get_current_user)):
    la_colection = db_client["caja_fuerte"]
    el_colection = db_client["banco"]
    fecha = date.today().strftime("%Y-%m-%d")

    documento = la_colection.find_one({"_id": ObjectId("67c9df85d9a7614d7993da52")})
    a_ingresar = documento.get("total", 0)

    dacument = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
    viejo_total = dacument.get("total", 0)
    
    nuevo_total = (viejo_total) + (a_ingresar)

    la_colection.update_one(
            {"_id": ObjectId("67c9df85d9a7614d7993da52")},
            {"$set": {"total": 0}}
            )
    
    el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": nuevo_total}}
            )
    
    ingresos_banco_dict = {"fecha": fecha, "pedido": "transferencia_a_banco_desde_caja_fuerte", "notas": None, "total": a_ingresar, "tipo_de_ingreso": "Banco"}
    db_client.ingresos_banco.insert_one(ingresos_banco_dict)
    return RedirectResponse("/dashboard/finanzas/fuerte", status_code=302)

@router.post("/abonacion")
async def abonar_machin(id: str = Form(...), fecha: str = Form(...), cliente: str = Form(...), total: int = Form(...), notas: str = Form(...), pago: str = Form(...), current_user: User = Depends(get_current_user)):
    mexico = db_client["prestamos"]
    la_colection = db_client["capital"]
    el_colection = db_client["banco"]

    documento = mexico.find_one({"_id": ObjectId(id)})
    viejo_total = documento.get("total", 0)
    nuevo_total = (viejo_total) - (total)

    es_proveedor = documento.get("colaborador", 0)
    es_activo = documento.get("tipo_de_pago", 0)
    las_notas = documento.get("notas", "nohaynotas")
    if es_proveedor == "Proveedores":
        prestamo_dict1 = {"fecha": fecha, "tipo_de_pago": f"se abonó {total} por última vez", "pedido": "abono_de_prestamo", "colaborador": "Proveedores", "abono_realizado_por": cliente, "total": nuevo_total, "notas": las_notas, "cantidad_abonada": total}
        mexico.find_one_and_replace({"_id": ObjectId(id)}, prestamo_dict1)
        user_dict1 = {"id": "1", "fecha": fecha, "pedido": "abono_de_prestamo", "tipo_de_pago": None, "abono_realizado_por": cliente, "notas": las_notas, "total": total,
                     "tipo_de_egreso": "Caja"}
        user_dict2 = {"id": "1", "fecha": fecha, "pedido": "abono_de_prestamo", "tipo_de_pago": None, "abono_realizado_por": cliente, "notas": las_notas, "total": total,
                     "tipo_de_egreso": "Banco"}
        del user_dict1["id"]
        del user_dict2["id"]

        if pago == "Caja":
            documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_capital.insert_one(user_dict1)
        if pago == "Banco":
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_banco.insert_one(user_dict2)
        return RedirectResponse("/historia_de_los_prestamos", status_code=302)
    
    if es_activo == "Activo adquirido":
        prestamo_dict2 = {"fecha": fecha, "tipo_de_pago": f"Activo adquirido (se abonó {total} por última vez)", "pedido": "abono_de_prestamo", "abono_realizado_por": cliente, "total": nuevo_total, "notas": las_notas, "cantidad_abonada": total}
        mexico.find_one_and_replace({"_id": ObjectId(id)}, prestamo_dict2)

        user_dict1 = {"id": "1", "fecha": fecha, "pedido": "abono_de_prestamo", "tipo_de_pago": None, "abono_realizado_por": cliente, "notas": las_notas, "total": total,
                     "tipo_de_egreso": "Caja"}
        user_dict2 = {"id": "1", "fecha": fecha, "pedido": "abono_de_prestamo", "tipo_de_pago": None, "abono_realizado_por": cliente, "notas": las_notas, "total": total,
                     "tipo_de_egreso": "Banco"}
        del user_dict1["id"]
        del user_dict2["id"]

        if pago == "Caja":
            documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            la_colection.update_one(
            {"_id": ObjectId("67c8a0921e6d92973db9307c")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_capital.insert_one(user_dict1)
        if pago == "Banco":
            documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
            cantidad_antaño = documento.get("total", 0)
            la_nueva_cantidad = (cantidad_antaño) - (total)
            el_colection.update_one(
            {"_id": ObjectId("67c89fa41e6d92973db9307b")},
            {"$set": {"total": la_nueva_cantidad}}
            )
            db_client.egresos_banco.insert_one(user_dict2)
        return RedirectResponse("/historia_de_los_prestamos", status_code=302)

    prestamo_dict = {"fecha": fecha, "tipo_de_pago": f"se abonó {total} por última vez", "abono_realizado_por": cliente, "total": nuevo_total, "notas": las_notas, "cantidad_abonada": total}
    
    mexico.find_one_and_replace({"_id": ObjectId(id)}, prestamo_dict)

    user_dict1 = {"id": "1", "fecha": fecha, "pedido": "abono_de_prestamo", "tipo_de_pago": None, "abono_realizado_por": cliente, "notas": las_notas, "total": total,
                     "tipo_de_egreso": "Caja"}
    user_dict2 = {"id": "1", "fecha": fecha, "pedido": "abono_de_prestamo", "tipo_de_pago": None, "abono_realizado_por": cliente, "notas": las_notas, "total": total,
                     "tipo_de_egreso": "Banco"}
    del user_dict1["id"]
    del user_dict2["id"]

    if pago == "Caja":
        documento = la_colection.find_one({"_id": ObjectId("67c8a0921e6d92973db9307c")})
        cantidad_antaño = documento.get("total", 0)
        la_nueva_cantidad = (cantidad_antaño) - (total)
        la_colection.update_one(
        {"_id": ObjectId("67c8a0921e6d92973db9307c")},
        {"$set": {"total": la_nueva_cantidad}}
        )
        db_client.egresos_capital.insert_one(user_dict1)
    if pago == "Banco":
        documento = el_colection.find_one({"_id": ObjectId("67c89fa41e6d92973db9307b")})
        cantidad_antaño = documento.get("total", 0)
        la_nueva_cantidad = (cantidad_antaño) - (total)
        el_colection.update_one(
        {"_id": ObjectId("67c89fa41e6d92973db9307b")},
        {"$set": {"total": la_nueva_cantidad}}
        )
        db_client.egresos_banco.insert_one(user_dict2)

    return RedirectResponse("/historia_de_los_prestamos", status_code=302)

@router.post("/edita_el_almacen_de_una")
async def cambia_el_valor_de_almacen(fecha: str = Form(...), cantidad: int = Form(...), current_user: User = Depends(get_current_user)):
    calection = db_client["almacen"]

    calection.update_one(
        {"_id": ObjectId("67cfa2cf5da5961fe45717ff")},
        {"$set": {"total": cantidad, "fecha": fecha}}
    )
    
    return RedirectResponse("/historia_de_las_compras", status_code=302)

@router.post("/elimina_el_prestamo")
async def eliminar_el_prestamo_mams(id: str = Form(...), current_user: User = Depends(get_current_user)):
    coleccion = db_client["prestamos"]

    pago = coleccion.delete_one({"_id": ObjectId(id)})

    if pago.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pedido no encontrado o no autorizado")
    
    return RedirectResponse("/historia_de_los_prestamos", status_code=302)
    

