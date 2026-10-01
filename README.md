# JobRADAR 📡

Un radar de ofertas de trabajo: revisa las páginas de empleo de varias empresas cada 15 minutos y te manda una notificación al teléfono apenas aparece una oferta nueva que te interesa. Así puedes aplicar en las primeras horas, antes de que la oferta acumule miles de candidatos.

- Filtra por **país** y por **área** (software, datos, IT, etc.), usando las categorías de cada empresa o palabras clave en el título.
- Avisa **solo de lo nuevo**: recuerda las ofertas que ya te notificó.
- Corre **gratis en GitHub Actions**, sin servidor, sin base de datos y sin credenciales.
- Las notificaciones llegan por **[ntfy](https://ntfy.sh)**; el correo es opcional.

---

## Cómo funciona

```
 GitHub Actions (cron cada 15 min)
        │
        ▼
   job_check.py ──► un crawler por empresa ──► API pública de empleos de la empresa
        │                    │
        │                    ▼
        │           filtros: país → categorías → palabras clave del título
        │                    │
        │                    ▼
        │           data/seen_jobs.json  (¿ya se notificó?)
        │                    │ solo las nuevas
        │                    ▼
        │           ntfy (push)  +  correo (opcional)
        ▼
   commit de data/seen_jobs.json de vuelta al repo
```

1. `job_check.py` hace una pasada por todas las empresas configuradas.
2. Cada crawler consulta la API de empleos de la empresa (la misma que usa su página de empleos) y devuelve las ofertas como `company / title / number / link / location`.
3. Se descartan las que no son del país configurado, las que no están en las categorías pedidas y las que no tienen ninguna de las palabras clave en el título.
4. `database/job_store.py` compara contra `data/seen_jobs.json` y se queda solo con las que nunca se habían visto.
5. Las nuevas se notifican, agrupadas por empresa, y el workflow hace commit del archivo actualizado para la siguiente corrida.

### Plataformas soportadas

La mayoría de las empresas no tienen un sistema propio: publican sus ofertas en una plataforma de reclutamiento. Por eso hay un crawler por plataforma, y agregar una empresa nueva normalmente es solo configuración.

| Plataforma | Crawler | Qué necesita en `urls.json` |
|---|---|---|
| Workday (`*.myworkdayjobs.com`) | `workday_crawler.py` | `tenant`, `site` |
| Eightfold (`*.eightfold.ai`) | `eightfold_crawler.py` | `host`, `domain` y, opcional, `job_page` |
| Greenhouse | `greenhouse_crawler.py` | `board` y, opcional, `locations` |
| Radancy / TalentBrew | `radancy_crawler.py` | `host` y, opcional, `language` |
| APIs propias | `amazon_crawler.py`, `ibm_crawler.py` | según el crawler |

En Workday y Radancy, el filtro de país y las categorías se buscan **por nombre** en cada corrida. Los IDs internos cambian con el tiempo, así que nunca se escriben a mano.

---

## Configuración: `job_crawlers-main/urls/urls.json`

```json
{
    "country": "Costa Rica",
    "companies": {
        "MiEmpresa": [
            {
                "tenant": "miempresa.wd5",
                "site": "miempresa/External",
                "max_jobs": 100,
                "categories": ["Software Engineering", "Information Technology"]
            },
            {
                "tenant": "miempresa.wd5",
                "site": "miempresa/External",
                "categories": ["Engineering", "Interns"],
                "title_keywords": ["software", "developer", "data", "IT", "cloud"]
            }
        ]
    }
}
```

- **`country`**: el país que filtran todos los crawlers.
- **Cada empresa es una lista de búsquedas.** Se ejecutan todas y una oferta que aparezca en dos búsquedas se notifica una sola vez.
- **`categories`**: deja solo las ofertas de esas categorías, usando **la taxonomía de la propia empresa** (Workday le dice *job family*, Eightfold *department*, Greenhouse *department*, Radancy *category*). El nombre tiene que coincidir exactamente. Si quitas la clave, recibes todas las ofertas del país.
- **`title_keywords`**: deja solo las ofertas cuyo título contiene alguna de las palabras. Se comparan como palabras completas, así que `IT` no coincide con `Digital`. Ojo: `cyber` tampoco coincide con `Cybersecurity`, así que pon las dos.
- Si una búsqueda tiene `categories` y `title_keywords`, la oferta tiene que cumplir **las dos**. Eso sirve para categorías mezcladas: por ejemplo, en "Engineering" quedarse solo con los títulos que suenan a software, como en el ejemplo de arriba.
- **`max_jobs`**: cuántas ofertas revisar como máximo por búsqueda (100 por defecto).
- **`locations`** (Greenhouse): nombres de oficina que cuentan como el país, para las empresas que nombran la oficina solo por la ciudad (por ejemplo `["Costa Rica", "San José"]`).

### ¿Qué categorías existen?

Corre una revisión y lee el log. Cada crawler imprime lo que descartó:

```
MiEmpresa: ignored jobs in Finance (3), Supply Chain (2)
MiEmpresa: ignored 4 job(s) whose title matched no keyword
```

Esos nombres son los que puedes agregar a `categories`.

---

## Notificaciones

### Push con ntfy (el canal principal)

ntfy no necesita cuenta ni token: el **nombre del topic es la dirección**. Escoge uno que nadie pueda adivinar, instala la app de ntfy (Android, iOS o web) y suscríbete a ese topic.

```bash
NTFY_TOPIC=job-radar-<algo-aleatorio>
NTFY_SERVER=https://ntfy.sh   # opcional, por si usas un servidor propio
```

Cada notificación trae:
- **Título**: cuántas ofertas nuevas hay y de qué empresa.
- **Cuerpo**: cada oferta con su ubicación y su link. ntfy limita los mensajes a 4KB, así que se muestran hasta 8 ofertas y luego "...and N more".
- **Al tocarla**: se abre la primera oferta.

Para ver el historial reciente sin la app (ntfy lo guarda unas 12 horas):

```bash
curl -s "https://ntfy.sh/<tu-topic>/json?poll=1&since=all"
```

### Correo (opcional)

Es la única parte que usa credenciales, así que solo se activa si las defines. `JOB_RADAR_EMAIL_PASSWORD` tiene que ser una [contraseña de aplicación](https://myaccount.google.com/apppasswords) de Gmail, nunca la contraseña de tu cuenta.

```bash
JOB_RADAR_EMAIL=tu@gmail.com
JOB_RADAR_EMAIL_PASSWORD=tu_app_password
JOB_RADAR_DEFAULT_RECEIVER=tu@gmail.com
```

---

## Ponerlo a correr en la nube (GitHub Actions)

`.github/workflows/job-radar.yml` corre `job_check.py` cada 15 minutos:

1. Sube el proyecto a tu propio repositorio de GitHub. **Tiene que ser público**: el job se salta en repos privados para que nunca se cobren minutos.
2. En *Settings → Secrets and variables → Actions → Variables*, crea la variable `NTFY_TOPIC` con tu topic. Es una variable y no un secreto a propósito: es una dirección, no una credencial.
3. En la pestaña *Actions*, abre **Job Radar** y dale *Run workflow* para probarlo. De ahí en adelante corre solo.

Después de cada corrida, el workflow hace commit de `data/seen_jobs.json` ("Remember the jobs already notified") usando el `GITHUB_TOKEN` que GitHub genera para el job.

Algunas cosas que conviene saber:
- GitHub encola los cron en runners compartidos, así que en la práctica corre cada 20–30 minutos, no exactamente cada 15.
- GitHub desactiva los workflows programados después de 60 días sin actividad en el repo. Te avisa por correo y se reactiva con un clic.
- Cada corrida tiene un tope de 10 minutos y usa un runner estándar (los grandes se cobran incluso en repos públicos).
- Solo instala `requests`: los crawlers no necesitan nada más.

---

## Correrlo en tu máquina

### Una sola revisión

```bash
cd job_crawlers-main
pip install requests
NTFY_TOPIC=job-radar-<algo-aleatorio> python job_check.py
```

Para probar sin ensuciar el historial real, apunta el almacén a otro archivo:

```bash
cp data/seen_jobs.json /tmp/seen.json
JOB_RADAR_STORE=/tmp/seen.json python job_check.py
```

Si no defines `NTFY_TOPIC`, se salta el push y el log solo dice cuántas ofertas nuevas encontró por empresa. Aun así **las marca como vistas** en el archivo que uses, así que para probar usa siempre una copia.

### Con el frontend y el backend (opcional)

Hay una página sencilla donde pones tu correo y arranca un revisor local cada 15 minutos. No es necesaria si usas GitHub Actions.

**Backend** (Flask, en `http://localhost:5000`):

```bash
cd job_crawlers-main
pip install -r requirement.txt
python app.py
```

- `POST /main` con `{"email": "tu@gmail.com"}`: hace una revisión inmediata y luego una cada 15 minutos. Es lo que llama el botón del frontend.
- `GET /check_new_job?email=...`: hace una sola revisión en el momento.

**Frontend** (React, en `http://localhost:3000`, requiere Node.js):

```bash
cd job-crawler-frontend
npm install
npm start
```

---

## Ofertas ya vistas: `data/seen_jobs.json`

Guarda, por empresa, los identificadores de las ofertas que ya se notificaron. Así no hace falta una base de datos.

- **Borra el archivo** (o la entrada de una empresa) para que te vuelvan a llegar todas las ofertas abiertas.
- **Cuando agregas una empresa nueva**, la primera corrida te notifica todas sus ofertas abiertas que pasen los filtros, no solo las que salgan desde ese momento.

---

## Agregar una empresa

**Si usa una plataforma soportada** (casi siempre):
1. Averigua la plataforma: abre una oferta de su página de empleos y mira a dónde lleva el botón de aplicar (`myworkdayjobs.com`, `eightfold.ai`, `greenhouse.io`...).
2. Agrega sus búsquedas a `urls.json`.
3. Regístrala en `PLATFORM_CRAWLERS` dentro de `job_check.py`, con el crawler de su plataforma.
4. Corre una revisión con `JOB_RADAR_STORE` apuntando a una copia y ajusta `categories` y `title_keywords` según lo que diga el log.

**Si tiene su propio sistema:**
1. Crea un crawler en `crawlers/` que devuelva una lista de dicts con `company`, `title`, `number` (un identificador estable), `link` y `location`.
2. Pásale esa lista a `publish_new_jobs(company, jobs, receiverEmail)` de `crawlers/common.py`: esa función se encarga de recordar las ofertas y notificar.
3. Regístralo en `CRAWLERS` dentro de `job_check.py`.

---

## Estructura del proyecto

```
.github/workflows/job-radar.yml   cron de GitHub Actions
job_crawlers-main/
├── job_check.py                  una pasada por todas las empresas (lo que corre el cron)
├── app.py                        backend Flask opcional, con su propio planificador
├── urls/urls.json                país, empresas y filtros
├── data/seen_jobs.json           ofertas ya notificadas
├── crawlers/
│   ├── common.py                 lectura de la config, filtro por palabras clave, publish_new_jobs
│   ├── workday_crawler.py        ┐
│   ├── eightfold_crawler.py      │ un crawler por plataforma
│   ├── greenhouse_crawler.py     │
│   ├── radancy_crawler.py        ┘
│   └── *_crawler.py              crawlers de una empresa concreta
├── database/job_store.py         lectura y escritura de seen_jobs.json
├── notifications/                push por ntfy y formato de los títulos
└── email_config/email_setup.py   correo opcional por Gmail
job-crawler-frontend/             página React opcional
```

Los crawlers que importan `database/mongo.py` o `config_crawler.py` (Selenium), y la carpeta `back_up_codes/`, son del proyecto original. No están conectados a `job_check.py`.

---

## Créditos y licencia

Basado en [JobCrawler](https://github.com/DevanshuBrahmbhatt/job_crawlers), un proyecto open source de estudiantes. No garantiza entrevistas ni que las ofertas estén completas o sean exactas. Úsalo bajo tu propio criterio.

Licencia **MIT**.
