import { useState, ReactNode } from 'react'
import { Lock } from 'lucide-react'
import toast from 'react-hot-toast'
import { Btn, Card, inputCls, Label, PageHeader } from '../components/ui'

const Section = ({ title, text, children, onSave }: { title: string; text?: string; children: ReactNode; onSave?: () => void }) =>
  <Card className="p-5"><h2 className="font-semibold">{title}</h2>{text && <p className="mb-4 text-sm text-slate-500">{text}</p>}<div className="grid gap-3 sm:grid-cols-2">{children}</div>{onSave && <div className="mt-4"><Btn variant="primary" onClick={onSave}>Save changes</Btn></div>}</Card>
export default function SettingsPage() {
  const [co, setCo] = useState({ name: 'Atlas Trading International SARL', tax: 'NIF 000116001234567', country: 'Algeria', address: 'Zone Industrielle, Tizi Ouzou' })
  const [me, setMe] = useState({ name: 'Yasmine Benali', email: 'y.benali@atlas-trading.example', role: 'Customs compliance officer' })
  const [n, setN] = useState({ review: true, incomplete: true, digest: false })
  const [app, setApp] = useState({ dateFormat: 'DD/MM/YYYY', pageSize: '8', lang: 'English' })
  const [ai, setAi] = useState({ provider: 'Managed by backend', threshold: '0.80' })
  const ok = (m: string) => () => toast.success(m)
  return <><PageHeader title="Settings" text="Local preferences are stored in this session only until the backend is connected." />
    <div className="space-y-4">
      <Section title="Company profile" onSave={ok('Company profile saved')}>{(['name', 'tax', 'country', 'address'] as const).map(k => <Label key={k} text={{ name: 'Company name', tax: 'Tax ID', country: 'Country', address: 'Address' }[k]}><input className={inputCls} value={co[k]} onChange={e => setCo({ ...co, [k]: e.target.value })} /></Label>)}</Section>
      <Section title="User profile" onSave={ok('Profile saved')}>{(['name', 'email', 'role'] as const).map(k => <Label key={k} text={{ name: 'Full name', email: 'Email', role: 'Role' }[k]}><input className={inputCls} type={k === 'email' ? 'email' : 'text'} value={me[k]} onChange={e => setMe({ ...me, [k]: e.target.value })} /></Label>)}</Section>
      <Section title="Notification preferences" onSave={ok('Notification preferences saved')}>{([['review', 'Documents that need review'], ['incomplete', 'Incomplete documents'], ['digest', 'Daily summary email']] as const).map(([k, l]) =>
        <label key={k} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={n[k]} onChange={e => setN({ ...n, [k]: e.target.checked })} />{l}</label>)}</Section>
      <Section title="AI provider" text="Provider, model and credentials are configured on the server by an administrator. This app never stores or displays API keys." onSave={ok('Saved (placeholder: nothing is sent to a backend yet)')}>
        <Label text="Provider"><div className="relative"><Lock className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" /><input disabled className={inputCls + ' bg-slate-50 pl-8'} value={ai.provider} readOnly /></div></Label>
        <Label text="Flag as uncertain below confidence"><input className={inputCls} type="number" min="0" max="1" step="0.05" value={ai.threshold} onChange={e => setAi({ ...ai, threshold: e.target.value })} /></Label></Section>
      <Section title="Application preferences" onSave={ok('Preferences saved')}>
        <Label text="Date format"><select className={inputCls} value={app.dateFormat} onChange={e => setApp({ ...app, dateFormat: e.target.value })}><option>DD/MM/YYYY</option><option>YYYY-MM-DD</option><option>MM/DD/YYYY</option></select></Label>
        <Label text="Rows per page"><select className={inputCls} value={app.pageSize} onChange={e => setApp({ ...app, pageSize: e.target.value })}><option>8</option><option>20</option><option>50</option></select></Label>
        <Label text="Language"><select className={inputCls} value={app.lang} onChange={e => setApp({ ...app, lang: e.target.value })}><option>English</option><option>Français</option></select></Label></Section>
    </div></>
}
