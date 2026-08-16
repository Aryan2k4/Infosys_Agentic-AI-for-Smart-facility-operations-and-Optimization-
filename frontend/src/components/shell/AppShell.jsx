import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Zap, Wrench, Users, ShieldCheck, Radio } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'
import ThemeToggle from '../ui/ThemeToggle'

const NAV_ITEMS = [
  {
    to: '/energy', label: 'Energy', code: 'EN', Icon: Zap,
    activeClass: 'text-blue-700 dark:text-blue-300',
    pillClass: 'bg-blue-500/10 dark:bg-blue-400/10',
    dotClass: 'bg-blue-500 dark:bg-blue-400',
  },
  {
    to: '/maintenance', label: 'Maintenance', code: 'MT', Icon: Wrench,
    activeClass: 'text-teal-700 dark:text-teal-300',
    pillClass: 'bg-teal-500/10 dark:bg-teal-400/10',
    dotClass: 'bg-teal-500 dark:bg-teal-400',
  },
  {
    to: '/occupancy', label: 'Occupancy', code: 'OC', Icon: Users,
    activeClass: 'text-violet-700 dark:text-violet-300',
    pillClass: 'bg-violet-500/10 dark:bg-violet-400/10',
    dotClass: 'bg-violet-500 dark:bg-violet-400',
  },
  {
    to: '/security', label: 'Security', code: 'SC', Icon: ShieldCheck,
    activeClass: 'text-rose-700 dark:text-rose-300',
    pillClass: 'bg-rose-500/10 dark:bg-rose-400/10',
    dotClass: 'bg-rose-500 dark:bg-rose-400',
  },
]

export default function AppShell({ children }) {
  const { theme } = useTheme()

  return (
    <div className="min-h-screen flex bg-paper dark:bg-graphite transition-colors duration-200">
      <aside className="w-[76px] md:w-[240px] shrink-0 border-r border-slate-200 dark:border-slate-800/80
                         bg-paper-raised dark:bg-panel flex flex-col">
        <div className="h-[80px] flex items-center justify-center md:justify-start md:px-5 gap-3 border-b border-slate-200 dark:border-slate-800/80">
          <motion.div
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 260, damping: 18 }}
            className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 via-blue-500 to-violet-600
                       flex items-center justify-center shrink-0 shadow-lg shadow-teal-500/20"
          >
            <Zap size={18} className="text-white" fill="currentColor" strokeWidth={0} />
          </motion.div>
          <div className="hidden md:block leading-tight">
            <div className="font-display text-base font-bold text-ink dark:text-slate-100 tracking-tight">
              Infosys<span className="text-teal-500 dark:text-teal-400">_</span>Agentic AI
            </div>
            <div className="font-mono text-[9px] tracking-[0.2em] text-slate-400 dark:text-slate-600">
              SMART FACILITY OPS
            </div>
          </div>
        </div>

        <nav className="flex-1 py-5 flex flex-col gap-1.5 px-3">
          {NAV_ITEMS.map((item) => {
            const Icon = item.Icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors relative overflow-hidden
                   ${isActive
                     ? item.activeClass
                     : 'text-slate-500 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-panel-raised hover:text-ink dark:hover:text-slate-300'}`
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <motion.span
                        layoutId="nav-pill"
                        transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                        className={`absolute inset-0 rounded-xl ${item.pillClass}`}
                      />
                    )}
                    <span className="relative z-10 flex items-center gap-3 w-full">
                      <span className={`shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-colors
                                        ${isActive ? item.pillClass : 'bg-transparent'}`}>
                        <Icon size={16} strokeWidth={2.1} />
                      </span>
                      <span className="hidden md:inline font-body text-sm font-medium">{item.label}</span>
                      {isActive && (
                        <motion.span
                          layoutId="nav-dot"
                          className={`hidden md:inline ml-auto w-1.5 h-1.5 rounded-full ${item.dotClass}`}
                        />
                      )}
                      {!isActive && (
                        <span className="hidden md:inline ml-auto font-mono text-[9px] text-slate-300 dark:text-slate-700">
                          {item.code}
                        </span>
                      )}
                    </span>
                  </>
                )}
              </NavLink>
            )
          })}
        </nav>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800/80">
          <div className="hidden md:flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-panel-raised border border-slate-200 dark:border-slate-800">
            <div className="relative shrink-0">
              <Radio size={14} className="text-teal-500 dark:text-teal-400" />
              <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-teal-500 dark:bg-teal-400 animate-pulse-line" />
            </div>
            <div className="leading-tight">
              <div className="font-mono text-[9px] tracking-widest text-slate-500 dark:text-slate-400">SYSTEM LIVE</div>
              <div className="font-mono text-[8px] text-slate-400 dark:text-slate-600">4 agents online</div>
            </div>
            <div className="ml-auto">
              <ThemeToggle />
            </div>
          </div>
          <div className="md:hidden flex justify-center">
            <ThemeToggle />
          </div>
        </div>
      </aside>

      <main className="flex-1 min-w-0">{children}</main>
    </div>
  )
}
