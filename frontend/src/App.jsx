import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowDownLeft, ArrowRight, ArrowUpRight, BarChart3, Bell, Camera, Check, ChevronRight,
  CircleDollarSign, Clock3, Egg, FileText, Home, Landmark, Leaf, LockKeyhole, LogOut,
  Menu, Minus, PawPrint, PiggyBank, Plus, ReceiptText, RefreshCw, ScanLine, Settings,
  ShieldCheck, Sparkles, TrendingDown, TrendingUp, Upload, UserRound, WalletCards, X
} from 'lucide-react'
import { api, newIdempotencyKey } from './api'

const money = new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC', maximumFractionDigits: 0 })
const shortDate = new Intl.DateTimeFormat('es-CR', { day: 'numeric', month: 'short' })
const longDate = new Intl.DateTimeFormat('es-CR', { weekday: 'long', day: 'numeric', month: 'long' })
const todayIso = () => new Date().toLocaleDateString('en-CA', { timeZone: 'America/Costa_Rica' })
const getResults = data => Array.isArray(data) ? data : (data?.results || [])

function Logo({ compact = false }) {
  return <div className={`logo ${compact ? 'compact' : ''}`}>
    <div className="logo-mark"><Home size={compact ? 19 : 24} strokeWidth={2.4}/><Leaf className="logo-leaf" size={12}/></div>
    {!compact && <div><strong>Casa Yeison</strong><span>Finanzas en familia</span></div>}
  </div>
}

function Login({ onLogin }) {
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = useCallback(async value => {
    if (value.length !== 4 || loading) return
    setLoading(true); setError('')
    try {
      const data = await api('/auth/pin/', { method: 'POST', body: JSON.stringify({ pin: value }) })
      localStorage.setItem('casa_yeison_token', data.token)
      onLogin()
    } catch (e) {
      setError(e.message); setPin('')
    } finally { setLoading(false) }
  }, [loading, onLogin])

  const tap = value => {
    if (value === 'delete') { setPin(p => p.slice(0, -1)); setError(''); return }
    if (pin.length >= 4) return
    const next = pin + value
    setPin(next); setError('')
    if (next.length === 4) setTimeout(() => submit(next), 180)
  }

  return <main className="login-page">
    <div className="login-orb orb-one"/><div className="login-orb orb-two"/>
    <section className="login-card animate-rise">
      <Logo />
      <div className="login-icon"><LockKeyhole size={26}/></div>
      <h1>Bienvenido, Yeison</h1>
      <p>Ingresa tu PIN para entrar a tu espacio familiar.</p>
      <div className={`pin-dots ${error ? 'shake' : ''}`}>
        {[0,1,2,3].map(i => <span key={i} className={i < pin.length ? 'filled' : ''}/>) }
      </div>
      <div className="keypad">
        {[1,2,3,4,5,6,7,8,9].map(n => <button key={n} onClick={() => tap(String(n))} disabled={loading}>{n}</button>)}
        <span/><button onClick={() => tap('0')} disabled={loading}>0</button>
        <button className="key-delete" onClick={() => tap('delete')} disabled={loading}><X size={21}/></button>
      </div>
      <div className="login-feedback">
        {loading ? <><span className="spinner"/> Verificando...</> : error || (import.meta.env.VITE_SHOW_DEV_PIN === 'true' ? 'PIN inicial local: 2580' : 'Acceso privado y protegido')}
      </div>
      <div className="secure-note"><ShieldCheck size={15}/> Tus datos permanecen protegidos</div>
    </section>
  </main>
}

function Header({ page, onMenu }) {
  const titles = { home: 'Mi hogar', movements: 'Movimientos', scan: 'Escanear factura', animals: 'Mis animales', more: 'Más opciones' }
  return <header className="topbar">
    <button className="desktop-menu" onClick={onMenu}><Menu size={21}/></button>
    <div><span className="eyebrow">Casa Yeison</span><h1>{titles[page]}</h1></div>
    <button className="avatar" aria-label="Perfil">Y</button>
  </header>
}

const navItems = [
  ['home', Home, 'Inicio'], ['movements', WalletCards, 'Movimientos'], ['scan', ScanLine, 'Escanear'],
  ['animals', PawPrint, 'Animales'], ['more', Menu, 'Más']
]

function Navigation({ page, setPage, open, setOpen }) {
  return <>
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-head"><Logo/><button onClick={() => setOpen(false)}><X/></button></div>
      <nav>{navItems.map(([id, Icon, label]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => { setPage(id); setOpen(false) }}><Icon size={20}/><span>{label}</span>{page === id && <i/>}</button>)}</nav>
      <div className="sidebar-foot"><ShieldCheck size={18}/><div><strong>Espacio privado</strong><span>Protegido con PIN</span></div></div>
    </aside>
    {open && <div className="scrim" onClick={() => setOpen(false)}/>}
    <nav className="bottom-nav">{navItems.map(([id, Icon, label]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => setPage(id)}><Icon size={21}/><span>{label}</span></button>)}</nav>
  </>
}

function StatCard({ label, value, icon: Icon, tone, hint }) {
  return <article className={`stat-card ${tone}`}>
    <div className="stat-icon"><Icon size={19}/></div><span>{label}</span><strong>{money.format(Number(value || 0))}</strong>
    {hint && <small>{hint}</small>}
  </article>
}

function Empty({ icon: Icon = FileText, title, text }) {
  return <div className="empty"><div><Icon size={24}/></div><strong>{title}</strong><span>{text}</span></div>
}

function Skeleton() { return <div className="skeleton-stack"><i/><i/><i/></div> }

function Dashboard({ data, loading, refresh, go }) {
  if (loading && !data) return <section className="page"><Skeleton/></section>
  const d = data || { month: {}, animals: {}, recent_transactions: [], recommendations: [], next_income: {} }
  const payDate = d.next_income?.date ? shortDate.format(new Date(`${d.next_income.date}T12:00:00`)) : '—'
  return <section className="page dashboard animate-page">
    <div className="welcome-row"><div><p>{longDate.format(new Date())}</p><h2>Hola, Yeison <span>👋</span></h2></div><button className="icon-button" onClick={refresh}><RefreshCw size={18}/></button></div>

    <article className="balance-card">
      <div className="balance-glow"/><div className="balance-top"><span>Disponible este mes</span><span className="balance-badge"><ShieldCheck size={13}/> Familiar</span></div>
      <strong>{money.format(Number(d.month?.balance || 0))}</strong>
      <div className="balance-meta"><span><ArrowDownLeft size={16}/><i>Ingresos</i><b>{money.format(Number(d.month?.income || 0))}</b></span><span><ArrowUpRight size={16}/><i>Gastos</i><b>{money.format(Number(d.month?.expenses || 0))}</b></span></div>
    </article>

    <div className="section-heading"><div><h3>Resumen</h3><p>Todo lo importante de un vistazo</p></div></div>
    <div className="stats-grid">
      <StatCard label="En animales" value={d.animals?.invested} icon={PiggyBank} tone="clay" hint="Inversión total"/>
      <StatCard label="Próximo ingreso" value={d.next_income?.amount} icon={Clock3} tone="blue" hint={payDate}/>
    </div>

    <div className="dashboard-columns">
      <div>
        <div className="section-heading"><div><h3>Movimientos recientes</h3><p>Tu actividad más reciente</p></div><button onClick={() => go('movements')}>Ver todos <ChevronRight size={16}/></button></div>
        <div className="list-card">
          {d.recent_transactions?.length ? d.recent_transactions.map(tx => <TransactionRow key={tx.id} tx={tx}/>) : <Empty icon={ReceiptText} title="Aún no hay gastos" text="Agrega tu primer movimiento para verlo aquí."/>}
        </div>
      </div>
      <div>
        <div className="section-heading"><div><h3>Consejos para hoy</h3><p>Máximo 5 recomendaciones al día</p></div><Sparkles size={18} className="sparkle"/></div>
        <div className="tips-card">
          {d.recommendations?.length ? d.recommendations.map((tip, i) => <div className="tip" key={tip.id}><span>{i + 1}</span><p>{tip.content}</p></div>) : <div className="tip"><span><Sparkles size={14}/></span><p>Tu resumen se prepara todos los días a las 12:00 m.</p></div>}
        </div>
      </div>
    </div>
  </section>
}

function TransactionRow({ tx }) {
  const income = tx.transaction_type === 'income'
  const Icon = income ? ArrowDownLeft : ArrowUpRight
  return <div className="transaction-row">
    <div className={`transaction-icon ${income ? 'income' : 'expense'}`} style={{ '--cat': tx.category?.color }}><Icon size={18}/></div>
    <div className="transaction-main"><strong>{tx.description}</strong><span>{tx.category?.name || 'Sin categoría'} · {shortDate.format(new Date(`${tx.date}T12:00:00`))}</span></div>
    <div className={`transaction-amount ${income ? 'income' : ''}`}>{income ? '+' : '−'}{money.format(Number(tx.amount)).replace('₡', '₡')}</div>
  </div>
}

function Modal({ title, children, onClose }) {
  useEffect(() => { const close = e => e.key === 'Escape' && onClose(); window.addEventListener('keydown', close); return () => window.removeEventListener('keydown', close) }, [onClose])
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}><div className="modal-sheet animate-sheet"><div className="modal-head"><div><span className="eyebrow">Casa Yeison</span><h2>{title}</h2></div><button onClick={onClose}><X size={21}/></button></div>{children}</div></div>
}

function Field({ label, children, hint }) { return <label className="field"><span>{label}</span>{children}{hint && <small>{hint}</small>}</label> }

function TransactionForm({ categories, initial = {}, onSaved, onClose }) {
  const [form, setForm] = useState({ transaction_type: 'expense', amount: '', description: '', date: todayIso(), category_id: '', note: '', status: 'completed', source: 'manual', ...initial })
  const [saving, setSaving] = useState(false)
  const set = (key, value) => setForm(f => ({ ...f, [key]: value }))
  const filtered = categories.filter(c => c.kind === form.transaction_type)
  const submit = async e => {
    e.preventDefault(); setSaving(true)
    try {
      const payload = { ...form, amount: String(form.amount), category_id: form.category_id ? Number(form.category_id) : null }
      if (!payload.receipt_id) delete payload.receipt_id
      await api('/transactions/', { method: 'POST', headers: { 'Idempotency-Key': newIdempotencyKey() }, body: JSON.stringify(payload) })
      onSaved('Movimiento guardado correctamente'); onClose()
    } catch (err) { onSaved(err.message, true) } finally { setSaving(false) }
  }
  return <form className="form" onSubmit={submit}>
    <div className="segmented"><button type="button" className={form.transaction_type === 'expense' ? 'active expense' : ''} onClick={() => set('transaction_type', 'expense')}><TrendingDown size={17}/> Gasto</button><button type="button" className={form.transaction_type === 'income' ? 'active income' : ''} onClick={() => set('transaction_type', 'income')}><TrendingUp size={17}/> Ingreso</button></div>
    <Field label="Monto en colones"><div className="money-input"><span>₡</span><input inputMode="decimal" required min="1" placeholder="0" value={form.amount} onChange={e => set('amount', e.target.value)}/></div></Field>
    <Field label="Descripción"><input required maxLength="180" placeholder="Ej. Compra del supermercado" value={form.description} onChange={e => set('description', e.target.value)}/></Field>
    <div className="form-grid"><Field label="Fecha"><input type="date" required value={form.date} onChange={e => set('date', e.target.value)}/></Field><Field label="Categoría"><select value={form.category_id} onChange={e => set('category_id', e.target.value)}><option value="">Sin categoría</option>{filtered.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field></div>
    <Field label="Nota opcional"><textarea rows="3" placeholder="Agrega un detalle que quieras recordar" value={form.note} onChange={e => set('note', e.target.value)}/></Field>
    <button className="primary-button" disabled={saving}>{saving ? <><span className="spinner"/> Guardando...</> : <><Check size={18}/> Guardar movimiento</>}</button>
  </form>
}

function Movements({ categories, notify, refreshDashboard }) {
  const [items, setItems] = useState([]), [loading, setLoading] = useState(true), [filter, setFilter] = useState('all'), [showForm, setShowForm] = useState(false)
  const load = useCallback(async () => { setLoading(true); try { const q = filter === 'all' ? '' : `?type=${filter}`; setItems(getResults(await api(`/transactions/${q}`))) } catch(e) { notify(e.message, true) } finally { setLoading(false) } }, [filter, notify])
  useEffect(() => { load() }, [load])
  const saved = (message, error) => { notify(message, error); if (!error) { load(); refreshDashboard() } }
  return <section className="page animate-page">
    <div className="page-intro"><div><p>Ingresos y gastos</p><h2>Tu dinero, en orden</h2></div><button className="add-button" onClick={() => setShowForm(true)}><Plus size={19}/> <span>Agregar</span></button></div>
    <div className="filter-pills">{[['all','Todos'],['expense','Gastos'],['income','Ingresos']].map(([id,label]) => <button key={id} className={filter === id ? 'active' : ''} onClick={() => setFilter(id)}>{label}</button>)}</div>
    <div className="list-card movements-list">{loading ? <Skeleton/> : items.length ? items.map(tx => <TransactionRow key={tx.id} tx={tx}/>) : <Empty icon={WalletCards} title="Sin movimientos" text="Cuando agregues movimientos aparecerán aquí."/>}</div>
    {showForm && <Modal title="Nuevo movimiento" onClose={() => setShowForm(false)}><TransactionForm categories={categories} onSaved={saved} onClose={() => setShowForm(false)}/></Modal>}
  </section>
}

function Scanner({ categories, notify, refreshDashboard, go }) {
  const input = useRef(), [image, setImage] = useState(null), [preview, setPreview] = useState(''), [scanning, setScanning] = useState(false), [result, setResult] = useState(null)
  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview])
  const choose = file => { if (!file) return; if (preview) URL.revokeObjectURL(preview); setImage(file); setPreview(URL.createObjectURL(file)); setResult(null) }
  const scan = async () => {
    if (!image) return; setScanning(true)
    const form = new FormData(); form.append('image', image)
    try { setResult(await api('/receipts/scan/', { method: 'POST', body: form })) } catch(e) { notify(e.message, true) } finally { setScanning(false) }
  }
  const saved = (message, error) => { notify(message, error); if (!error) { refreshDashboard(); go('home') } }
  if (result) return <section className="page scan-page animate-page"><div className="scan-success"><div><Check size={22}/></div><span>Lectura terminada</span><strong>Revisa los datos antes de guardar</strong><small>Precisión estimada: {result.confidence}%</small></div><div className="scan-form-card"><TransactionForm categories={categories} initial={{ amount: result.total || '', description: result.merchant || '', date: result.receipt_date || todayIso(), receipt_id: result.id, source: 'receipt' }} onSaved={saved} onClose={() => setResult(null)}/></div></section>
  return <section className="page scan-page animate-page">
    <div className="page-intro"><div><p>Factura a movimiento</p><h2>Escanea y revisa</h2></div></div>
    <div className={`scanner-frame ${preview ? 'has-image' : ''}`} onClick={() => !preview && input.current.click()}>
      {preview ? <img src={preview} alt="Factura seleccionada"/> : <><div className="scan-corners"/><div className="camera-circle"><Camera size={31}/></div><h3>Fotografía tu factura</h3><p>Procura buena luz y que se vea completa.</p><button type="button"><Upload size={17}/> Elegir fotografía</button></>}
      {scanning && <div className="scan-overlay"><i/><div><span className="spinner"/> Leyendo factura...</div></div>}
    </div>
    <input ref={input} hidden type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={e => choose(e.target.files?.[0])}/>
    {preview && <div className="scan-actions"><button className="secondary-button" onClick={() => input.current.click()}><RefreshCw size={17}/> Cambiar</button><button className="primary-button" onClick={scan} disabled={scanning}><ScanLine size={18}/> Escanear factura</button></div>}
    <div className="privacy-card"><ShieldCheck size={20}/><div><strong>Tu factura es privada</strong><span>La imagen se usa únicamente para completar el formulario.</span></div></div>
  </section>
}

function AnimalForm({ notify, onDone, initial, title = 'Nueva inversión' }) {
  const [form, setForm] = useState(initial || { name: 'Inversión general de animales', purchase_amount: '', purchase_date: todayIso(), status: 'active', note: '' }), [saving, setSaving] = useState(false)
  const set = (k,v) => setForm(f => ({...f,[k]:v}))
  const submit = async e => { e.preventDefault(); setSaving(true); try { const method = initial?.id ? 'PATCH' : 'POST'; const path = initial?.id ? `/animals/${initial.id}/` : '/animals/'; await api(path,{method,body:JSON.stringify(form)}); notify(initial?.id ? 'Venta registrada correctamente' : 'Inversión guardada'); onDone() } catch(e) { notify(e.message,true) } finally { setSaving(false) } }
  return <form className="form" onSubmit={submit}>
    {!initial?.id && <><Field label="Nombre"><input required maxLength="120" value={form.name} onChange={e=>set('name',e.target.value)}/></Field><div className="form-grid"><Field label="Monto de compra"><div className="money-input"><span>₡</span><input required min="1" inputMode="decimal" value={form.purchase_amount} onChange={e=>set('purchase_amount',e.target.value)}/></div></Field><Field label="Fecha de compra"><input required type="date" value={form.purchase_date} onChange={e=>set('purchase_date',e.target.value)}/></Field></div></>}
    {initial?.id && <div className="sale-origin"><PawPrint size={19}/><div><span>Inversión original</span><strong>{money.format(Number(initial.purchase_amount))}</strong></div></div>}
    {initial?.id && <div className="form-grid"><Field label="Monto de venta"><div className="money-input"><span>₡</span><input required min="1" inputMode="decimal" value={form.sale_amount || ''} onChange={e=>set('sale_amount',e.target.value)}/></div></Field><Field label="Fecha de venta"><input required type="date" value={form.sale_date || todayIso()} onChange={e=>set('sale_date',e.target.value)}/></Field></div>}
    <Field label="Nota opcional"><textarea rows="3" value={form.note || ''} onChange={e=>set('note',e.target.value)} placeholder="Ej. Compra de cerdos y pollos"/></Field>
    <button className="primary-button" disabled={saving}><Check size={18}/>{saving ? 'Guardando...' : title}</button>
  </form>
}

function Animals({ notify, refreshDashboard }) {
  const [items,setItems]=useState([]),[loading,setLoading]=useState(true),[modal,setModal]=useState(null)
  const load=useCallback(async()=>{setLoading(true);try{setItems(getResults(await api('/animals/')))}catch(e){notify(e.message,true)}finally{setLoading(false)}},[notify])
  useEffect(()=>{load()},[load])
  const invested=items.reduce((s,x)=>s+Number(x.purchase_amount||0),0), profit=items.filter(x=>x.profit!==null).reduce((s,x)=>s+Number(x.profit),0)
  const done=()=>{setModal(null);load();refreshDashboard()}
  return <section className="page animate-page">
    <div className="page-intro"><div><p>Inversión familiar</p><h2>Animales</h2></div><button className="add-button" onClick={()=>setModal('add')}><Plus size={19}/><span>Agregar</span></button></div>
    <div className="animal-hero"><div><span>Total invertido</span><strong>{money.format(invested)}</strong><small>{items.filter(x=>x.status==='active').length} inversiones activas</small></div><div className="pig-illustration"><PiggyBank size={45}/><Leaf size={21}/></div></div>
    <div className="stats-grid"><StatCard label="Ganancia realizada" value={profit} icon={TrendingUp} tone="green" hint="Venta − compra"/><StatCard label="Inversiones" value={items.length} icon={PawPrint} tone="clay" hint="Registro general"/></div>
    <div className="section-heading"><div><h3>Historial</h3><p>Compras y ventas de animales</p></div></div>
    <div className="list-card">{loading?<Skeleton/>:items.length?items.map(item=><div className="animal-row" key={item.id}><div className="animal-row-icon"><PawPrint size={19}/></div><div><strong>{item.name}</strong><span>Compra {shortDate.format(new Date(`${item.purchase_date}T12:00:00`))}</span></div><div className="animal-values"><strong>{money.format(Number(item.purchase_amount))}</strong>{item.status==='active'?<button onClick={()=>setModal(item)}>Registrar venta</button>:<span className={Number(item.profit)>=0?'gain':'loss'}>{Number(item.profit)>=0?'+':''}{money.format(Number(item.profit))}</span>}</div></div>):<Empty icon={PawPrint} title="Sin inversiones todavía" text="Registra una compra de animales para comenzar."/>}</div>
    {modal&&<Modal title={modal==='add'?'Nueva inversión':'Registrar venta'} onClose={()=>setModal(null)}><AnimalForm notify={notify} onDone={done} initial={modal==='add'?null:{...modal,status:'sold',sale_date:todayIso()}} title={modal==='add'?'Guardar inversión':'Completar venta'}/></Modal>}
  </section>
}

function More({ notify, onLogout, refreshDashboard }) {
  const [eggs,setEggs]=useState(''),[records,setRecords]=useState([]),[saving,setSaving]=useState(false)
  const load=useCallback(async()=>{try{setRecords(getResults(await api('/eggs/')))}catch(e){notify(e.message,true)}},[notify])
  useEffect(()=>{load()},[load])
  const save=async e=>{e.preventDefault();setSaving(true);try{const existing=records.find(x=>x.date===todayIso());await api(existing?`/eggs/${existing.id}/`:'/eggs/',{method:existing?'PATCH':'POST',body:JSON.stringify({date:todayIso(),quantity:Number(eggs)})});notify('Cantidad de huevos guardada');setEggs('');load();refreshDashboard()}catch(e){notify(e.message,true)}finally{setSaving(false)}}
  const todayRecord=records.find(x=>x.date===todayIso())
  const menu=[['Seguridad','PIN y protección de acceso',ShieldCheck],['Notificaciones','Resumen diario a las 12:00 m.',Bell],['Datos familiares','Yeison y Camila · Fondo único',UserRound],['Configuración','Colones costarricenses',Settings]]
  return <section className="page animate-page">
    <div className="page-intro"><div><p>Hogar y configuración</p><h2>Más opciones</h2></div></div>
    <article className="egg-card"><div className="egg-art"><Egg size={31}/></div><div className="egg-copy"><span>Huevos de hoy</span><strong>{todayRecord?.quantity || 0}</strong><small>unidades registradas</small></div><form onSubmit={save}><input aria-label="Cantidad de huevos" type="number" required min="0" max="10000" placeholder={todayRecord?.quantity || '0'} value={eggs} onChange={e=>setEggs(e.target.value)}/><button disabled={saving}><Check size={17}/></button></form></article>
    <div className="section-heading"><div><h3>Tu espacio</h3><p>Preferencias de Casa Yeison</p></div></div>
    <div className="settings-list">{menu.map(([title,text,Icon])=><button key={title}><span><Icon size={19}/></span><div><strong>{title}</strong><small>{text}</small></div><ChevronRight size={18}/></button>)}</div>
    <button className="logout-button" onClick={onLogout}><LogOut size={18}/> Cerrar sesión</button>
    <p className="version">Casa Yeison · Versión 1.0 local</p>
  </section>
}

function Toast({ toast }) { return toast ? <div className={`toast ${toast.error?'error':''}`}><span>{toast.error?<X size={16}/>:<Check size={16}/>}</span>{toast.message}</div> : null }

export default function App() {
  const [authenticated,setAuthenticated]=useState(Boolean(localStorage.getItem('casa_yeison_token')))
  const [page,setPage]=useState('home'),[navOpen,setNavOpen]=useState(false),[dashboard,setDashboard]=useState(null),[loading,setLoading]=useState(true),[categories,setCategories]=useState([]),[toast,setToast]=useState(null)
  const toastTimer=useRef()
  const notify=useCallback((message,error=false)=>{clearTimeout(toastTimer.current);setToast({message,error});toastTimer.current=setTimeout(()=>setToast(null),3500)},[])
  const loadDashboard=useCallback(async()=>{if(!authenticated)return;setLoading(true);try{setDashboard(await api('/dashboard/'))}catch(e){if(!e.message.includes('autoriz'))notify(e.message,true)}finally{setLoading(false)}},[authenticated,notify])
  const loadCategories=useCallback(async()=>{if(!authenticated)return;try{setCategories(getResults(await api('/categories/')))}catch(e){notify(e.message,true)}},[authenticated,notify])
  useEffect(()=>{const expired=()=>setAuthenticated(false);window.addEventListener('casa-auth-expired',expired);return()=>window.removeEventListener('casa-auth-expired',expired)},[])
  useEffect(()=>{if(authenticated){loadDashboard();loadCategories()}},[authenticated,loadDashboard,loadCategories])
  const logout=async()=>{try{await api('/auth/logout/',{method:'POST'})}catch{}localStorage.removeItem('casa_yeison_token');setAuthenticated(false);setPage('home')}
  if(!authenticated)return <Login onLogin={()=>setAuthenticated(true)}/>
  return <div className="app-shell">
    <Navigation page={page} setPage={setPage} open={navOpen} setOpen={setNavOpen}/>
    <div className="main-shell"><Header page={page} onMenu={()=>setNavOpen(true)}/><main className="content">
      {page==='home'&&<Dashboard data={dashboard} loading={loading} refresh={loadDashboard} go={setPage}/>}
      {page==='movements'&&<Movements categories={categories} notify={notify} refreshDashboard={loadDashboard}/>}
      {page==='scan'&&<Scanner categories={categories} notify={notify} refreshDashboard={loadDashboard} go={setPage}/>}
      {page==='animals'&&<Animals notify={notify} refreshDashboard={loadDashboard}/>}
      {page==='more'&&<More notify={notify} onLogout={logout} refreshDashboard={loadDashboard}/>}
    </main></div><Toast toast={toast}/>
  </div>
}
