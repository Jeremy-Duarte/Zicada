# Zicada - Tienda de Ropa

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Jeremy-Duarte_Zicada&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Jeremy-Duarte_Zicada)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![Astro](https://img.shields.io/badge/Astro-5.x-BC52EE?logo=astro&logoColor=white)](https://astro.build)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.x-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![SonarCloud](https://img.shields.io/badge/SonarCloud-Quality%20Gate-F3702A?logo=sonarcloud&logoColor=white)](https://sonarcloud.io/summary/new_code?id=Jeremy-Duarte_Zicada)

---

## Sobre el proyecto

Zicada es una tienda online de ropa diseñada para personas que no siguen reglas establecidas y utilizan la moda como una forma de expresión personal.

El sistema permite a los clientes explorar catálogos por colecciones temáticas, personalizar su compra, pagar contraentrega y hacer seguimiento de sus pedidos. Los administradores gestionan productos, inventario y pedidos; los repartidores utilizan una aplicación PWA offline para organizar sus entregas en ruta.

> *"La moda se va, tu estilo permanece"*

---

## Misión

Diseñar y comercializar prendas streetwear que reflejen identidad, actitud y autenticidad, dirigidas a personas que no siguen reglas establecidas y utilizan la moda como una forma de expresión personal.

## Visión

Posicionar a Zicada como una marca reconocida a nivel nacional, con proyección internacional, por su autenticidad, versatilidad y capacidad de adaptarse a diferentes estilos sin perder su esencia.

---

## Características principales

| Modulo | Funcionalidades |
|--------|----------------|
| Catalogo | Productos de fabrica, colecciones limitadas con estilos visuales unicos, filtros por talla, precio y categoria |
| Carrito | Añadir, quitar y modificar cantidades, persistencia local, checkout sin registro |
| Pedidos | Pago contraentrega, estados (pendiente, confirmado, preparando, listo, en camino, entregado), token de seguimiento |
| Entregas (PWA) | Login de repartidor, pedidos del dia, mapa, llamada y WhatsApp, modo offline, resumen de caja |
| Administracion | CRUD de productos, colecciones, tallas, stock, pedidos, usuarios y reportes |
| Seguridad | Roles (Administrador y Entregador), auditoria con created_by y updated_by, soft delete |

---

## Tecnologias utilizadas

| Capa | Tecnologia | Version |
|------|------------|---------|
| Backend | Django + Django REST Framework | 6.x |
| Base de datos | PostgreSQL (produccion) / SQLite (desarrollo) | 15.x |
| Frontend web | Astro + Tailwind CSS | 5.x / 3.x |
| App movil | PWA (offline-first) | - |
| Hosting | Vercel (frontend) / Railway (backend) | - |
| Almacenamiento imagenes | Cloudinary | - |
| Calidad de codigo | SonarCloud | - |
| Variables de entorno | django-environ | - |

## Dependencias

Las versiones exactas de las dependencias de Python se encuentran en el archivo [`requirements.txt`](requirements.txt).

---

## Como empezar (desarrollo local)

### 1. Clonar el repositorio

```bash
git clone https://github.com/Jeremy-Duarte/Zicada.git
cd Zicada
```

### 2. Crear y activar entorno virtual

```bash
python -m venv .venv
```

**Windows**
```bash
.venv\Scripts\activate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar el archivo `.env` con tus datos (secret key, base de datos, email, etc.)

### 5. Generar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Ejecutar migraciones

```bash
python manage.py migrate
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Iniciar servidor de desarrollo

```bash
python manage.py runserver
```

---

## Roles del sistema

| Rol | Descripcion |
|-----|-------------|
| Administrador | Dueños de Zicada. Acceso total al panel web. Gestionan productos, colecciones, pedidos y usuarios. |
| Entregador | Repartidores (pueden ser los mismos dueños). Acceso a la PWA: ven pedidos del dia y marcan entregados o pagados. |
| Cliente | Comprador sin registro. Navega catalogo, compra y consulta estado del pedido con token. |

---

## Desarrollador

**Jeremy Duarte**  
Tecnologo en Desarrollo de Software

---

## Licencia

Proyecto privado. No autorizado su uso, reproduccion o distribucion sin consentimiento explicito.

---

## Enlaces utiles

- [SonarCloud Dashboard](https://sonarcloud.io/summary/new_code?id=Jeremy-Duarte_Zicada)

---

*Ultima actualizacion: Abril 2026*