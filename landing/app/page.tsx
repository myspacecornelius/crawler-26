"use client";

import { useState, useCallback, useEffect, useRef, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Check,
  User,
  Mail,
  RefreshCw,
  Linkedin,
  Info,
  ExternalLink,
  type LucideIcon,
} from "lucide-react";

/* ═══════════════════════════════════════════════════
   CUSTOM SVG ICONS — Brand visual language
   Hexagonal cells, network nodes, radar, dossiers,
   signal scoring, coverage routing
   ═══════════════════════════════════════════════════ */

function IconHexScan({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M12 2l5.2 3v6L12 14 6.8 11V5z" />
      <path d="M12 14v4" />
      <path d="M8 18h8" />
      <circle cx="12" cy="8" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  );
}

function IconNetworkNode({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="5" r="2" />
      <circle cx="5" cy="18" r="2" />
      <circle cx="19" cy="18" r="2" />
      <path d="M12 7v4" />
      <path d="M12 11l-5.5 5" />
      <path d="M12 11l5.5 5" />
      <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

function IconRadarSweep({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" />
      <path d="M12 12l6.36-6.36" />
      <circle cx="15" cy="9" r="1.25" fill="currentColor" stroke="none" opacity="0.6" />
    </svg>
  );
}

function IconDossier({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 7h8" />
      <path d="M8 11h5" />
      <path d="M8 15h3" />
      <circle cx="17" cy="14" r="2.5" />
      <path d="M15.5 16l-1 2" />
    </svg>
  );
}

function IconSignalScore({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect x="3" y="14" width="3" height="6" rx="0.5" />
      <rect x="8" y="10" width="3" height="10" rx="0.5" />
      <rect x="13" y="6" width="3" height="14" rx="0.5" />
      <rect x="18" y="3" width="3" height="17" rx="0.5" />
      <path d="M4.5 11l4-3.5 5 2 5-5" />
    </svg>
  );
}

function IconCoverageMap({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="8" cy="8" r="3" />
      <circle cx="17" cy="10" r="2.5" />
      <circle cx="10" cy="17" r="2" />
      <path d="M10.5 9.5l4.5 1" />
      <path d="M9 13.5l1-2" />
      <path d="M14.5 12l-3 3.5" />
    </svg>
  );
}

function IconRouteGraph({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="4" cy="12" r="2" />
      <circle cx="12" cy="5" r="2" />
      <circle cx="20" cy="12" r="2" />
      <circle cx="12" cy="19" r="2" />
      <path d="M6 11l4-4.5" />
      <path d="M14 6.5l4 4" />
      <path d="M18 13.5l-4 4" />
      <path d="M10 17.5L6 13.5" />
    </svg>
  );
}

function IconThesisMatch({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M12 2l5.2 3v6L12 14 6.8 11V5z" />
      <path d="M9.5 7.5l1.5 1.5 3-3" />
    </svg>
  );
}

function IconDeliverability({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 8l9 5 9-5" />
      <circle cx="18" cy="15" r="3" />
      <path d="M16.75 15l1 1 2-2" />
    </svg>
  );
}

function IconWarmPath({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="5" cy="12" r="2.5" />
      <circle cx="19" cy="12" r="2.5" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" opacity="0.4" />
      <path d="M7.5 12h3" />
      <path d="M13.5 12h3" />
      <path d="M12 8v-2" />
      <path d="M12 16v2" />
    </svg>
  );
}

function IconCheckSize({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M12 2l5.2 3v6L12 14 6.8 11V5z" />
      <path d="M10 7.5h4" />
      <path d="M12 5.5v4" />
    </svg>
  );
}

function IconRecentDeals({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3.5 3.5" />
      <circle cx="17" cy="7" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

function IconGeo({ className = "" }: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="10" r="3" />
      <path d="M12 2a8 8 0 0 0-8 8c0 5.4 8 12 8 12s8-6.6 8-12a8 8 0 0 0-8-8z" />
    </svg>
  );
}

/* ═══════════════════════════════════════════════════
   SVG PATTERNS & BRAND MARKS
   ═══════════════════════════════════════════════════ */

function HoneycombPattern({ opacity = 0.05, className = "" }: { opacity?: number; className?: string }) {
  return (
    <svg className={`absolute inset-0 w-full h-full pointer-events-none ${className}`} style={{ opacity }} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="hc" x="0" y="0" width="56" height="100" patternUnits="userSpaceOnUse">
          <path d="M28 66L0 50L0 16L28 0L56 16L56 50L28 66ZM28 100L0 84L0 50L28 34L56 50L56 84L28 100Z" fill="none" stroke="currentColor" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#hc)" />
    </svg>
  );
}

function HoneypotMark({ size = 28, className = "" }: { size?: number; className?: string }) {
  const s = size;
  const h = s * 0.866;
  return (
    <svg width={s * 1.5} height={h * 2} viewBox={`0 0 ${s * 1.5} ${h * 2}`} fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
      <polygon points={`${s * 0.75},0 ${s * 1.5},${h * 0.5} ${s * 1.5},${h * 1.5} ${s * 0.75},${h * 2} 0,${h * 1.5} 0,${h * 0.5}`} stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" fill="none" />
      <polygon points={`${s * 0.75},${h * 0.4} ${s * 1.1},${h * 0.7} ${s * 1.1},${h * 1.3} ${s * 0.75},${h * 1.6} ${s * 0.4},${h * 1.3} ${s * 0.4},${h * 0.7}`} fill="currentColor" opacity="0.2" stroke="currentColor" strokeWidth="1" strokeLinejoin="round" />
    </svg>
  );
}

function AvatarPlaceholder({ size = 40 }: { size?: number }) {
  return (
    <div className="rounded-full bg-border-subtle flex items-center justify-center flex-shrink-0 overflow-hidden" style={{ width: size, height: size }}>
      <User size={size * 0.5} strokeWidth={1.75} className="text-text-muted" />
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   CONSTANTS & TYPES
   ═══════════════════════════════════════════════════ */

const NAV_LINKS = [
  { label: "How it works", href: "#how-it-works" },
  { label: "What you get", href: "#what-you-get" },
  { label: "Proof", href: "#proof" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
] as const;

const PAIN_POINTS = [
  { pain: "Spray-and-pray outreach wastes months", solution: "Thesis-fit targeting narrows your list to investors who actually write your check size in your sector.", color: "border-l-danger" },
  { pain: "No idea who the right partner is", solution: "Partner-level data with investment history, so you pitch the person -- not just the firm.", color: "border-l-danger" },
  { pain: "Outreach copy that sounds like every other founder", solution: "Sequenced, personalized outreach built on what each investor actually cares about.", color: "border-l-danger" },
] as const;

const STEPS = [
  { number: "01", title: "Intake", description: "Tell us your stage, sector, geography, and round size. We calibrate the search to your raise.", Icon: IconDossier },
  { number: "02", title: "Build the target list", description: "We match thesis-fit investors at the partner level, enriched with check size, recent deals, and warm intro paths where possible.", Icon: IconRadarSweep },
  { number: "03", title: "Outreach system", description: "You get sequenced outreach copy, tracking guidance, and CRM-ready exports. We stay on as advisors through the raise.", Icon: IconRouteGraph },
] as const;

const DELIVERABLES = [
  { title: "Enriched VC lead list", detail: "Thesis-fit investors matched to your round, sector, and geography.", Icon: IconHexScan },
  { title: "Partner-level targeting", detail: "Individual partner names, roles, and investment focus -- not just firm pages.", Icon: IconNetworkNode },
  { title: "Check size + stage alignment", detail: "Only investors whose typical check and stage match your raise.", Icon: IconCheckSize },
  { title: "Geo + sector filters", detail: "Filter by city, region, or sector vertical. Global coverage, local precision.", Icon: IconGeo },
  { title: "Outreach copy + sequencing", detail: "Cold email templates and follow-up sequences calibrated to each tier.", Icon: IconRouteGraph },
  { title: "CRM-ready export", detail: "CSV or direct integration with your CRM. No reformatting needed.", Icon: IconDossier },
  { title: "Fresh signals weekly", detail: "New investors, updated contact info, and fresh deal signals delivered weekly.", Icon: IconRecentDeals },
  { title: "Advisory support", detail: "Office hours and async support from operators who have raised before.", Icon: IconWarmPath },
] as const;

interface EnrichCapability {
  Icon: ({ className }: { className?: string }) => JSX.Element;
  title: string;
  sub: string;
}

const ENRICH_CAPABILITIES: readonly EnrichCapability[] = [
  { Icon: IconNetworkNode, title: "Partner identity", sub: "Name, role, and LinkedIn profile" },
  { Icon: IconThesisMatch, title: "Thesis summary", sub: "Sector focus and investment keywords" },
  { Icon: IconCheckSize, title: "Check size + stage fit", sub: "Typical range and preferred stage" },
  { Icon: IconRecentDeals, title: "Recent investments", sub: "Deals made in the last 12 months" },
  { Icon: IconGeo, title: "Geo coverage", sub: "Office locations and geographic focus" },
  { Icon: IconDeliverability, title: "Deliverability + confidence", sub: "Verified, guessed, or inferred score" },
  { Icon: IconSignalScore, title: "Email deliverability status", sub: "MX validation and catch-all detection" },
  { Icon: IconWarmPath, title: "Warm intro path indicators", sub: "Shared connections where available" },
] as const;

const SAMPLE_FILTERS = [
  "Seed", "Series A", "Series B", "Pre-seed",
  "AI / ML", "Fintech", "Health tech", "Climate",
  "SaaS", "Developer tools", "Consumer", "Deep tech",
  "US only", "Europe", "APAC", "LatAm",
  "$500K--$2M", "$2M--$10M", "$10M+",
] as const;

interface Testimonial {
  quote: string;
  name: string;
  role: string;
  stage: string;
  city: string;
}

const TESTIMONIALS: readonly Testimonial[] = [
  { quote: "The biggest win wasn't more investors -- it was fewer, better ones. We stopped guessing and started running a process.", name: "Maya K.", role: "Founder", stage: "Seed", city: "NYC" },
  { quote: "Partner-level mapping saved weeks. The outreach kit was blunt and effective.", name: "Jon S.", role: "Founder", stage: "Series A", city: "SF" },
  { quote: "We replaced a spreadsheet mess with a clean pipeline and repeatable sequencing.", name: "Elena R.", role: "Head of BD", stage: "Growth", city: "London" },
  { quote: "It didn't promise magic. It gave us a tight target list and a system.", name: "Amir D.", role: "Founder", stage: "Pre-seed", city: "Austin" },
  { quote: "Filtering by check size + thesis prevented a lot of wasted outreach.", name: "Natalie P.", role: "Operator", stage: "Seed", city: "Boston" },
] as const;

interface CaseStudy {
  scenario: string;
  built: readonly string[];
  result: string;
  chips: readonly string[];
  stat: string;
  statLabel: string;
}

const CASE_STUDIES: readonly CaseStudy[] = [
  { scenario: "Seed SaaS founder raising $2M", built: ["Thesis-fit target list (140 funds)", "3-touch email sequence per tier", "CRM-ready CSV export"], result: "Reduced research from 3 weeks to 2 days. Founder focused outreach on 40 high-fit funds.", chips: ["CSV export", "Scoring rubric", "Outreach sequences"], stat: "3wk to 2d", statLabel: "Research time" },
  { scenario: "Series A devtools company", built: ["Partner-level mapping across 80 funds", "Stage + check size constraints applied", "Weekly refresh cadence"], result: "Eliminated 60% of initial list as poor fit. Outreach reply rate improved.", chips: ["Partner mapping", "Stage filter", "Weekly refresh"], stat: "60%", statLabel: "Poor fit removed" },
  { scenario: "Growth-stage fintech (Series B)", built: ["Geo-segmented lists (US + Europe)", "CRM integration with HubSpot", "Warm intro path indicators"], result: "Team ran parallel outreach across 2 geos. Reduced wasted meetings.", chips: ["Geo segmentation", "CRM integration", "Warm intros"], stat: "2 geos", statLabel: "Parallel outreach" },
  { scenario: "Repeat founder, second raise", built: ["Automated weekly target refresh", "Tracking + follow-up cadence", "Delta reports (new vs. stale leads)"], result: "Maintained a live pipeline across a 4-month raise without manual upkeep.", chips: ["Weekly refresh", "Delta tracking", "Cadence system"], stat: "4 months", statLabel: "Hands-free pipeline" },
] as const;

const PRICING_TIERS = [
  { name: "Starter", price: "$--", period: "/ month", description: "For founders exploring options", features: ["Up to 200 enriched leads", "Stage + sector filtering", "CRM-ready CSV export", "Email support"], cta: "Get started", highlighted: false },
  { name: "Growth", price: "$--", period: "/ month", description: "For founders actively raising", features: ["Up to 1,000 enriched leads", "Partner-level targeting", "Outreach copy + sequencing", "Fresh signals weekly", "Office hours access"], cta: "Request access", highlighted: true },
  { name: "Scale", price: "$--", period: "/ month", description: "For IR teams and repeat raisers", features: ["Unlimited enriched leads", "Custom thesis-fit scoring", "Warm intro path mapping", "Dedicated advisory support", "CRM integration", "Priority data requests"], cta: "Talk to us", highlighted: false },
] as const;

const COMPARISON_ROWS = [
  { feature: "Enriched leads", starter: "200", growth: "1,000", scale: "Unlimited" },
  { feature: "Partner-level contacts", starter: false, growth: true, scale: true },
  { feature: "Outreach copy + sequencing", starter: false, growth: true, scale: true },
  { feature: "Confidence score", starter: true, growth: true, scale: true, tooltip: "Each contact scored as verified, guessed, or inferred based on our validation pipeline." },
  { feature: "Refresh cadence", starter: "On request", growth: "Weekly", scale: "Daily", tooltip: "How often we re-validate contacts, update investment activity, and surface fresh signals." },
  { feature: "Warm intro indicators", starter: false, growth: false, scale: true, tooltip: "Shared connections, portfolio overlaps, and co-investor networks where detectable." },
  { feature: "Advisory support", starter: "Email", growth: "Office hours", scale: "Dedicated" },
  { feature: "CRM integration", starter: false, growth: false, scale: true },
] as const;

const FAQS = [
  { question: "What is included in enrichment?", answer: "Each lead includes the partner's name, role, LinkedIn, fund thesis, check size range, stage preference, recent investments, location, email (with confidence score), and warm intro path indicators where available." },
  { question: "How is thesis-fit determined?", answer: "We cross-reference your sector, stage, geography, and round size against each fund's stated thesis, portfolio history, and recent deal activity. Leads are scored and tiered by alignment strength." },
  { question: "How current is the data?", answer: "Our pipeline refreshes weekly. Contact info, investment activity, and fund focus areas are continuously validated against public filings, press, and direct web crawls." },
  { question: "Do you provide warm intros?", answer: "We identify warm intro paths where they exist -- shared connections, portfolio overlap, or co-investor networks. We do not broker intros directly, but we surface the signal for you to act on." },
  { question: "How do you handle compliance and privacy?", answer: "All data is sourced from publicly available information: fund websites, SEC filings, press releases, and public directories. We do not scrape private networks or purchase leaked databases." },
  { question: "What stage and sector do you support?", answer: "Pre-seed through Series B across all major sectors: SaaS, AI/ML, fintech, health tech, climate, developer tools, consumer, deep tech, and more. Growth-stage support available on the Scale plan." },
  { question: "Can I bring my own list and have you enrich it?", answer: "Yes. Upload your existing investor list and we will enrich it with partner-level contacts, thesis alignment scores, and outreach-ready data. Available on all plans." },
] as const;

const STAGES = ["Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Not sure yet"] as const;
const SECTORS = ["AI / ML", "SaaS", "Fintech", "Health tech", "Climate", "Developer tools", "Consumer", "Deep tech", "Other"] as const;
type Stage = (typeof STAGES)[number];
type Sector = (typeof SECTORS)[number];

interface FormState {
  email: string;
  name: string;
  company: string;
  stage: Stage | "";
  sector: Sector | "";
  raising90Days: boolean;
}

/* ═══════════════════════════════════════════════════
   PRIMITIVES
   ═══════════════════════════════════════════════════ */

function Container({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`max-w-container mx-auto px-6 ${className}`}>{children}</div>;
}

function Section({ children, id, className = "" }: { children: ReactNode; id?: string; className?: string }) {
  return (
    <motion.section id={id} className={`py-16 md:py-24 ${className}`} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }} transition={{ duration: 0.5, ease: "easeOut" }}>
      <Container>{children}</Container>
    </motion.section>
  );
}

function SectionTitle({ children, subtitle }: { children: ReactNode; subtitle?: string }) {
  return (
    <div className="mb-12 md:mb-16">
      <h2 className="text-[32px] leading-[1.2] font-[650] text-text-primary">{children}</h2>
      {subtitle && <p className="mt-3 text-base leading-relaxed text-text-secondary max-w-xl">{subtitle}</p>}
    </div>
  );
}

function UnderlineAccent({ children }: { children: ReactNode }) {
  return (
    <span className="relative inline-block">
      <span className="absolute bottom-[2px] left-[-4px] right-[-4px] h-[40%] rounded-[8px] -z-10 bg-honey-tint" />
      {children}
    </span>
  );
}

function Card({ children, className = "", hover = true }: { children: ReactNode; className?: string; hover?: boolean }) {
  return (
    <div className={`bg-surface-primary rounded-card border border-border-subtle shadow-card p-7 ${hover ? "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover" : ""} ${className}`}>
      {children}
    </div>
  );
}

function BrandIconBadge({ children, variant = "honey" }: { children: ReactNode; variant?: "honey" | "petrol" | "danger" }) {
  const bg = variant === "danger" ? "bg-danger/10" : variant === "petrol" ? "bg-petrol-mist" : "bg-honey-tint";
  const color = variant === "danger" ? "text-danger" : variant === "petrol" ? "text-petrol-600" : "text-honey-500";
  return (
    <div className={`w-9 h-9 rounded-xl ${bg} flex items-center justify-center flex-shrink-0 ${color}`}>
      {children}
    </div>
  );
}

function CheckBullet() {
  return (
    <div className="w-5 h-5 rounded-full bg-honey-tint flex items-center justify-center flex-shrink-0">
      <Check size={12} strokeWidth={2.5} className="text-honey-500" />
    </div>
  );
}

function TooltipInline({ text }: { text: string }) {
  const [show, setShow] = useState(false);
  return (
    <span className="relative inline-flex ml-1 cursor-help" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)} onFocus={() => setShow(true)} onBlur={() => setShow(false)} tabIndex={0} role="button" aria-label={text}>
      <Info size={13} strokeWidth={1.75} className="text-text-muted" />
      <AnimatePresence>
        {show && (
          <motion.span initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }} className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2.5 text-xs leading-relaxed text-charcoal-text bg-charcoal-900 rounded-lg shadow-lg border border-charcoal-border z-50">
            {text}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
}

function ButtonPrimary({ children, onClick, type = "button", disabled = false, className = "" }: { children: ReactNode; onClick?: () => void; type?: "button" | "submit"; disabled?: boolean; className?: string }) {
  return (
    <motion.button type={type} onClick={onClick} disabled={disabled} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className={`bg-honey-500 text-charcoal-900 font-semibold rounded-button px-5 py-3 text-[15px] hover:bg-honey-400 focus:outline-none focus:shadow-honey-ring disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 ${className}`}>
      {children}
    </motion.button>
  );
}

function ButtonSecondary({ children, onClick, href, className = "" }: { children: ReactNode; onClick?: () => void; href?: string; className?: string }) {
  const cls = `inline-flex items-center justify-center border border-text-primary/20 text-text-primary font-semibold rounded-button px-5 py-3 text-[15px] hover:bg-honey-tint transition-colors duration-150 ${className}`;
  if (href) return <a href={href} className={cls}>{children}</a>;
  return <button onClick={onClick} className={cls}>{children}</button>;
}

function Input({ label, id, type = "text", required = false, value, onChange, placeholder }: { label: string; id: string; type?: string; required?: boolean; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-text-primary mb-1.5">{label}{required && <span className="text-danger ml-0.5">*</span>}</label>
      <input id={id} name={id} type={type} required={required} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="w-full bg-white border border-border-strong rounded-button px-3 py-3 text-[15px] text-text-primary placeholder:text-text-muted focus:outline-none focus:border-honey-500 focus:ring-2 focus:ring-honey-glow transition-colors duration-150" aria-label={label} />
    </div>
  );
}

function Select({ label, id, value, onChange, options, placeholder = "Select..." }: { label: string; id: string; value: string; onChange: (v: string) => void; options: readonly string[]; placeholder?: string }) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-text-primary mb-1.5">{label}</label>
      <select id={id} name={id} value={value} onChange={(e) => onChange(e.target.value)} className="w-full bg-white border border-border-strong rounded-button px-3 py-3 text-[15px] text-text-primary focus:outline-none focus:border-honey-500 focus:ring-2 focus:ring-honey-glow transition-colors duration-150 appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%239A978F%22%20stroke-width%3D%222%22%3E%3Cpath%20d%3D%22m6%209%206%206%206-6%22%2F%3E%3C%2Fsvg%3E')] bg-[length:16px] bg-[right_12px_center] bg-no-repeat" aria-label={label}>
        <option value="">{placeholder}</option>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

function scrollToForm() {
  document.getElementById("final-cta")?.scrollIntoView({ behavior: "smooth" });
}

/* ═══════════════════════════════════════════════════
   DISTRIBUTED SOCIAL PROOF COMPONENTS
   ═══════════════════════════════════════════════════ */

function MicroProof({ testimonial, className = "" }: { testimonial: Testimonial; className?: string }) {
  return (
    <div className={`flex items-center gap-4 bg-surface-primary border border-border-subtle rounded-card px-6 py-4 shadow-sm ${className}`}>
      <div className="w-1 h-10 bg-petrol-600 rounded-full flex-shrink-0" />
      <blockquote className="text-sm text-text-secondary leading-relaxed italic flex-1">&ldquo;{testimonial.quote}&rdquo;</blockquote>
      <div className="flex items-center gap-2 flex-shrink-0">
        <AvatarPlaceholder size={32} />
        <div>
          <div className="text-xs font-semibold text-text-primary">{testimonial.name}</div>
          <div className="text-[10px] text-text-muted">{testimonial.role}, {testimonial.city}</div>
        </div>
      </div>
    </div>
  );
}

function SidecarTestimonial({ testimonial, stat, statLabel }: { testimonial: Testimonial; stat: string; statLabel: string }) {
  return (
    <div className="bg-petrol-700 rounded-card p-6 text-white">
      <div className="flex items-center gap-3 mb-4">
        <div className="text-3xl font-[700] text-honey-500">{stat}</div>
        <div className="text-xs text-white/50 uppercase tracking-wider leading-tight">{statLabel}</div>
      </div>
      <blockquote className="text-sm text-white/80 leading-relaxed mb-4">&ldquo;{testimonial.quote}&rdquo;</blockquote>
      <div className="flex items-center gap-2">
        <AvatarPlaceholder size={28} />
        <div>
          <div className="text-xs font-semibold text-white/90">{testimonial.name}</div>
          <div className="text-[10px] text-white/40">{testimonial.role} ({testimonial.stage}), {testimonial.city}</div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   NAVBAR
   ═══════════════════════════════════════════════════ */

function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-charcoal-900 border-b border-charcoal-border no-print">
      <Container>
        <div className="flex items-center justify-between h-16">
          <a href="#" className="flex items-center gap-2 text-charcoal-text">
            <HoneypotMark size={18} className="text-honey-500" />
            <span className="font-[650] text-lg tracking-tight">Honeypot</span>
          </a>
          <div className="hidden md:flex items-center gap-6">
            {NAV_LINKS.map((l) => <a key={l.href} href={l.href} className="text-charcoal-text/60 hover:text-charcoal-text text-sm font-medium transition-colors">{l.label}</a>)}
            <a href="#final-cta" className="text-charcoal-text/60 hover:text-charcoal-text text-sm font-medium transition-colors">Book a call</a>
            <ButtonPrimary onClick={scrollToForm}>Get the list</ButtonPrimary>
          </div>
          <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden text-charcoal-text p-2" aria-label="Toggle menu">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round">{mobileOpen ? <path d="M18 6L6 18M6 6l12 12" /> : <path d="M4 6h16M4 12h16M4 18h16" />}</svg>
          </button>
        </div>
        <AnimatePresence>
          {mobileOpen && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="md:hidden overflow-hidden border-t border-charcoal-border">
              <div className="py-4 flex flex-col gap-3">
                {NAV_LINKS.map((l) => <a key={l.href} href={l.href} onClick={() => setMobileOpen(false)} className="text-charcoal-text/60 hover:text-charcoal-text text-sm font-medium py-1">{l.label}</a>)}
                <ButtonPrimary onClick={() => { setMobileOpen(false); scrollToForm(); }} className="mt-2 w-full">Get the list</ButtonPrimary>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Container>
    </nav>
  );
}

/* ═══════════════════════════════════════════════════
   HERO + DATA PREVIEW
   ═══════════════════════════════════════════════════ */

const MOCK_DATA = {
  Seed: [
    { fund: "Forerunner Ventures", partner: "Eurie Kim", check: "$1--3M", location: "SF", sector: "Consumer", score: 94 },
    { fund: "Pear VC", partner: "Pejman Nozad", check: "$500K--2M", location: "Palo Alto", sector: "AI / SaaS", score: 91 },
    { fund: "Precursor Ventures", partner: "Charles Hudson", check: "$250K--1M", location: "SF", sector: "Fintech", score: 88 },
  ],
  "Series A": [
    { fund: "Bessemer Venture Partners", partner: "Mary D'Onofrio", check: "$5--15M", location: "NYC", sector: "SaaS", score: 96 },
    { fund: "Felicis Ventures", partner: "Aydin Senkut", check: "$3--10M", location: "SF", sector: "AI / ML", score: 93 },
    { fund: "Index Ventures", partner: "Sarah Cannon", check: "$5--20M", location: "London", sector: "Fintech", score: 90 },
  ],
  "Series B": [
    { fund: "Iconiq Growth", partner: "Matt Jacobson", check: "$20--50M", location: "SF", sector: "Enterprise", score: 97 },
    { fund: "Coatue Management", partner: "Thomas Laffont", check: "$15--40M", location: "NYC", sector: "AI / ML", score: 95 },
    { fund: "General Catalyst", partner: "Kyle Doherty", check: "$10--30M", location: "Boston", sector: "Health tech", score: 92 },
  ],
} as const;
type MockTab = keyof typeof MOCK_DATA;

function DataPreview() {
  const [activeTab, setActiveTab] = useState<MockTab>("Series A");
  const tabs: MockTab[] = ["Seed", "Series A", "Series B"];
  const rows = MOCK_DATA[activeTab];
  return (
    <div className="bg-petrol-700 rounded-[22px] p-[2px] shadow-xl shadow-petrol-glow ring-1 ring-petrol-600/30">
      <div className="bg-petrol-800/80 backdrop-blur-xl rounded-[20px] border border-white/10 overflow-hidden">
        <div className="px-4 pt-4 pb-3 border-b border-white/10">
          <div className="flex items-center gap-2 bg-white/10 rounded-button px-3 py-2">
            <Search size={14} strokeWidth={1.75} className="text-white/50" />
            <span className="text-white/40 text-sm">Search funds, partners, sectors...</span>
          </div>
        </div>
        <div className="flex gap-1 px-4 pt-3 pb-2">
          {tabs.map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-150 ${activeTab === tab ? "bg-honey-500/30 text-white" : "text-white/50 hover:text-white/70 hover:bg-white/5"}`}>{tab}</button>
          ))}
        </div>
        <div className="px-4 py-2 grid grid-cols-[1fr_0.8fr_0.6fr_0.5fr_0.4fr] gap-2 text-[10px] font-semibold text-white/40 uppercase tracking-wider border-b border-white/5">
          <span>Fund / Partner</span><span>Sector</span><span>Check</span><span>Location</span><span>Score</span>
        </div>
        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.2 }}>
            {rows.map((row, i) => (
              <div key={i} className="px-4 py-3 grid grid-cols-[1fr_0.8fr_0.6fr_0.5fr_0.4fr] gap-2 border-b border-white/5 last:border-0 hover:bg-white/[0.04] transition-colors">
                <div><div className="text-white text-xs font-semibold leading-snug">{row.fund}</div><div className="text-white/50 text-[10px]">{row.partner}</div></div>
                <div className="text-white/70 text-xs self-center">{row.sector}</div>
                <div className="text-white/70 text-xs self-center">{row.check}</div>
                <div className="text-white/70 text-xs self-center">{row.location}</div>
                <div className="self-center"><span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${row.score >= 95 ? "bg-honey-500/25 text-honey-400" : row.score >= 90 ? "bg-petrol-600/40 text-petrol-mist" : "bg-white/10 text-white/70"}`}>{row.score}</span></div>
              </div>
            ))}
          </motion.div>
        </AnimatePresence>
        <div className="px-4 py-2.5 border-t border-white/5 flex items-center justify-between">
          <span className="text-white/30 text-[10px]">Showing 3 of 12,542 leads</span>
          <span className="text-white/40 text-[10px] flex items-center gap-1">Updated daily <RefreshCw size={9} strokeWidth={1.75} /></span>
        </div>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section className="relative pt-28 pb-16 md:pt-36 md:pb-20 overflow-hidden">
      <HoneycombPattern opacity={0.06} className="text-text-primary" />
      <Container className="relative">
        <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center">
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <h1 className="text-[40px] md:text-[48px] leading-[1.10] font-[650] text-text-primary">
              Stop guessing which VCs{" "}<UnderlineAccent><span className="text-petrol-600">fit your raise.</span></UnderlineAccent>
            </h1>
            <p className="mt-5 text-base md:text-[17px] leading-relaxed text-text-secondary max-w-lg">Enriched, partner-level VC leads matched to your stage, sector, and geography -- with outreach copy, sequencing, and advisory support built in.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonPrimary onClick={scrollToForm}>Request access <ArrowRight size={16} strokeWidth={1.75} className="inline ml-1.5 -mt-0.5" /></ButtonPrimary>
              <ButtonSecondary href="#what-you-get">See what&apos;s included</ButtonSecondary>
            </div>
            <p className="mt-4 text-xs text-text-muted">No spam. 1--2 emails/week. Unsubscribe anytime.</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }} className="hidden md:block">
            <DataPreview />
          </motion.div>
        </div>
      </Container>
    </section>
  );
}

/* ═══════════════════════════════════════════════════
   MICRO-PROOF STRIP (below hero)
   ═══════════════════════════════════════════════════ */

function HeroProofStrip() {
  return (
    <div className="py-6 border-y border-border-subtle bg-surface-warm">
      <Container>
        <MicroProof testimonial={TESTIMONIALS[0]} />
      </Container>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   PROBLEM/SOLUTION
   ═══════════════════════════════════════════════════ */

function ProblemSolutionBand() {
  return (
    <Section>
      <SectionTitle subtitle="Most founders burn weeks on untargeted outreach. Here is how we fix that.">Common problems, specific solutions</SectionTitle>
      <div className="grid md:grid-cols-3 gap-6">
        {PAIN_POINTS.map((item, i) => (
          <div key={i} className="bg-surface-primary rounded-card border border-border-subtle shadow-card p-7 border-l-[3px] border-l-danger/60">
            <p className="text-sm text-text-primary font-medium mb-5">{item.pain}</p>
            <div className="w-8 h-px bg-border-strong mb-5" />
            <p className="text-sm text-text-secondary leading-relaxed">{item.solution}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   HOW IT WORKS (horizontal stepper, not card grid)
   ═══════════════════════════════════════════════════ */

function HowItWorks() {
  return (
    <Section id="how-it-works" className="bg-surface-warm border-y border-border-subtle">
      <SectionTitle subtitle="Three steps from intake to outreach-ready investor list.">How it works</SectionTitle>
      <div className="grid md:grid-cols-3 gap-0 relative">
        {/* Connecting line */}
        <div className="hidden md:block absolute top-[28px] left-[16.7%] right-[16.7%] h-px bg-border-strong" />
        {STEPS.map((step, i) => (
          <div key={step.number} className="relative text-center px-6 py-2">
            <div className="relative z-10 w-14 h-14 mx-auto rounded-2xl bg-petrol-700 flex items-center justify-center mb-5 shadow-petrol-glow">
              <step.Icon className="text-petrol-mist w-6 h-6" />
            </div>
            <div className="text-[10px] font-semibold text-petrol-600 uppercase tracking-widest mb-2">Step {step.number}</div>
            <h3 className="text-[18px] font-semibold text-text-primary mb-2">{step.title}</h3>
            <p className="text-sm text-text-secondary leading-relaxed max-w-[280px] mx-auto">{step.description}</p>
          </div>
        ))}
      </div>
      {/* Sidecar testimonial after how it works */}
      <div className="mt-14 grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <MicroProof testimonial={TESTIMONIALS[1]} />
        </div>
        <SidecarTestimonial testimonial={TESTIMONIALS[3]} stat="40+" statLabel="Hours saved per raise" />
      </div>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   WHAT YOU GET
   ═══════════════════════════════════════════════════ */

function WhatYouGet() {
  return (
    <Section id="what-you-get">
      <SectionTitle subtitle="Everything you need to run a precise, operator-grade fundraising process.">What you get</SectionTitle>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {DELIVERABLES.map((d) => (
          <Card key={d.title} className="p-6">
            <BrandIconBadge variant="petrol">
              <d.Icon className="w-[18px] h-[18px]" />
            </BrandIconBadge>
            <h3 className="mt-4 text-[15px] font-semibold text-text-primary mb-1.5">{d.title}</h3>
            <p className="text-[13px] text-text-secondary leading-relaxed">{d.detail}</p>
          </Card>
        ))}
      </div>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   FEATURE DEEP DIVE (thesis-fit scoring artifact)
   ═══════════════════════════════════════════════════ */

function FeatureDeepDive() {
  return (
    <Section className="bg-surface-warm border-y border-border-subtle">
      <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center">
        <div className="bg-petrol-700 rounded-[18px] p-[2px] ring-1 ring-petrol-600/30 shadow-petrol-glow">
          <div className="bg-petrol-800/60 backdrop-blur-xl rounded-[16px] border border-white/10 p-5">
            <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-3">Thesis-fit scoring</div>
            {([
              { label: "Stage match", value: "Series A", ok: true },
              { label: "Sector overlap", value: "AI / ML, SaaS", ok: true },
              { label: "Check size", value: "$3--10M", ok: true },
              { label: "Geo preference", value: "US, Europe", ok: true },
              { label: "Recent activity", value: "2 deals in last 90d", ok: true },
              { label: "Warm path", value: "1 shared connection", ok: false },
            ] as const).map((r, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <span className="text-white/60 text-xs">{r.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-white/80 text-xs font-medium">{r.value}</span>
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center ${r.ok ? "bg-honey-500/25" : "bg-white/10"}`}>
                    <Check size={10} strokeWidth={2.5} className={r.ok ? "text-honey-400" : "text-white/30"} />
                  </div>
                </div>
              </div>
            ))}
            <div className="mt-4 flex items-center justify-between">
              <span className="text-white/40 text-[10px] uppercase tracking-wider">Composite score</span>
              <span className="text-lg font-bold text-honey-400">96</span>
            </div>
          </div>
        </div>
        <div>
          <h2 className="text-[32px] leading-[1.2] font-[650] text-text-primary mb-4">How <UnderlineAccent>targeting</UnderlineAccent> is determined</h2>
          <p className="text-base text-text-secondary leading-relaxed mb-6">Each investor is scored against your raise parameters. We weight six dimensions to surface the investors most likely to engage.</p>
          <ul className="space-y-4">
            {[
              { t: "Thesis alignment", d: "We compare your sector and stage against the fund's stated thesis and portfolio patterns." },
              { t: "Activity recency", d: "Funds that made deals in the last 90 days are weighted higher -- they are actively deploying." },
              { t: "Check size calibration", d: "We filter out investors whose typical check is too large or too small for your round." },
            ].map((item) => (
              <li key={item.t} className="flex items-start gap-3">
                <CheckBullet />
                <div><span className="text-sm font-semibold text-text-primary">{item.t}</span><p className="text-sm text-text-secondary leading-relaxed mt-0.5">{item.d}</p></div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   PROOF: ENRICHMENT CAPABILITIES + FILTERS
   ═══════════════════════════════════════════════════ */

function Proof() {
  return (
    <Section id="proof">
      <SectionTitle subtitle="What enriched actually means, and how it translates to better outreach.">Built for <UnderlineAccent>precision</UnderlineAccent>, not volume</SectionTitle>
      <div className="grid md:grid-cols-2 gap-8 mb-12">
        {/* Enrichment capabilities grid */}
        <div>
          <h3 className="text-[17px] font-semibold text-text-primary mb-5">What &quot;enriched&quot; means</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {ENRICH_CAPABILITIES.map((cap) => (
              <div key={cap.title} className="flex items-start gap-3 p-3 rounded-xl border border-border-subtle bg-surface-primary">
                <BrandIconBadge variant="honey">
                  <cap.Icon className="w-[18px] h-[18px]" />
                </BrandIconBadge>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-text-primary">{cap.title}</div>
                  <div className="text-xs text-text-muted leading-snug mt-0.5">{cap.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-6">
          <Card hover={false}>
            <h3 className="text-[17px] font-semibold text-text-primary mb-4">Thesis-fit filters</h3>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_FILTERS.map((f) => <span key={f} className="bg-surface-warm border border-border-subtle rounded-full px-2.5 py-1 text-xs text-text-secondary">{f}</span>)}
            </div>
          </Card>
          {/* Embedded proof testimonial */}
          <div className="bg-petrol-700 rounded-card p-5 text-white">
            <blockquote className="text-sm text-white/80 leading-relaxed mb-3">&ldquo;{TESTIMONIALS[4].quote}&rdquo;</blockquote>
            <div className="flex items-center gap-2">
              <AvatarPlaceholder size={28} />
              <div>
                <div className="text-xs font-semibold text-white/90">{TESTIMONIALS[4].name}</div>
                <div className="text-[10px] text-white/40">{TESTIMONIALS[4].role} ({TESTIMONIALS[4].stage}), {TESTIMONIALS[4].city}</div>
              </div>
            </div>
          </div>
          <Card hover={false}>
            <h3 className="text-[17px] font-semibold text-text-primary mb-3">Expected outcomes</h3>
            <ul className="space-y-2.5">
              {["Increases targeting precision by filtering to thesis-fit investors only", "Reduces wasted outreach to firms that do not invest at your stage or sector", "Saves 40+ hours of manual research per fundraise"].map((t) => (
                <li key={t} className="flex items-start gap-2.5"><Check size={14} strokeWidth={2} className="text-honey-500 mt-1 flex-shrink-0" /><span className="text-sm text-text-secondary">{t}</span></li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   CASE STUDIES (carousel with stat callouts)
   ═══════════════════════════════════════════════════ */

function CaseStudyCarousel() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [modalIdx, setModalIdx] = useState<number | null>(null);

  function scroll(dir: "left" | "right") {
    if (!scrollRef.current) return;
    const amount = 360;
    scrollRef.current.scrollBy({ left: dir === "right" ? amount : -amount, behavior: "smooth" });
  }

  return (
    <Section className="bg-surface-warm border-y border-border-subtle">
      <div className="flex items-end justify-between mb-8">
        <SectionTitle subtitle="How the system works across different stages and sectors.">Case studies</SectionTitle>
        <div className="hidden md:flex gap-2 mb-12">
          <button onClick={() => scroll("left")} className="w-10 h-10 rounded-full border border-border-strong flex items-center justify-center text-text-muted hover:text-text-primary hover:border-text-primary/30 transition-colors" aria-label="Scroll left"><ChevronLeft size={18} strokeWidth={1.75} /></button>
          <button onClick={() => scroll("right")} className="w-10 h-10 rounded-full border border-border-strong flex items-center justify-center text-text-muted hover:text-text-primary hover:border-text-primary/30 transition-colors" aria-label="Scroll right"><ChevronRight size={18} strokeWidth={1.75} /></button>
        </div>
      </div>
      <div ref={scrollRef} className="flex gap-5 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide -mx-6 px-6" style={{ scrollbarWidth: "none" }}>
        {CASE_STUDIES.map((cs, i) => (
          <div key={i} className="snap-start flex-shrink-0 w-[320px] md:w-[360px]">
            <Card className="h-full flex flex-col">
              {/* Stat callout */}
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border-subtle">
                <span className="text-2xl font-[700] text-petrol-600">{cs.stat}</span>
                <span className="text-[10px] text-text-muted uppercase tracking-wider leading-tight">{cs.statLabel}</span>
              </div>
              <h4 className="text-[15px] font-semibold text-text-primary mb-3">{cs.scenario}</h4>
              <ul className="space-y-1.5 mb-4">
                {cs.built.map((b) => (
                  <li key={b} className="flex items-start gap-2 text-sm text-text-secondary">
                    <Check size={13} strokeWidth={2} className="text-honey-500 mt-0.5 flex-shrink-0" />{b}
                  </li>
                ))}
              </ul>
              <p className="text-xs text-text-muted leading-relaxed mb-4 flex-1">{cs.result}</p>
              <div className="flex flex-wrap gap-1.5 mb-4">
                {cs.chips.map((c) => <span key={c} className="bg-surface-warm border border-border-subtle rounded-full px-2 py-0.5 text-[10px] text-text-muted">{c}</span>)}
              </div>
              <button onClick={() => setModalIdx(i)} className="inline-flex items-center gap-1 text-sm font-semibold text-text-primary hover:text-petrol-600 transition-colors">
                View case study <ExternalLink size={13} strokeWidth={1.75} />
              </button>
            </Card>
          </div>
        ))}
      </div>

      {/* Modal */}
      <AnimatePresence>
        {modalIdx !== null && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/50 backdrop-blur-sm" onClick={() => setModalIdx(null)}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="bg-surface-primary rounded-card shadow-xl max-w-lg w-full p-8" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border-subtle">
                <span className="text-3xl font-[700] text-petrol-600">{CASE_STUDIES[modalIdx].stat}</span>
                <span className="text-xs text-text-muted uppercase tracking-wider">{CASE_STUDIES[modalIdx].statLabel}</span>
              </div>
              <h3 className="text-xl font-semibold text-text-primary mb-4">{CASE_STUDIES[modalIdx].scenario}</h3>
              <ul className="space-y-2 mb-4">
                {CASE_STUDIES[modalIdx].built.map((b) => <li key={b} className="flex items-start gap-2 text-sm text-text-secondary"><Check size={13} strokeWidth={2} className="text-honey-500 mt-0.5 flex-shrink-0" />{b}</li>)}
              </ul>
              <p className="text-sm text-text-secondary mb-6">{CASE_STUDIES[modalIdx].result}</p>
              <button onClick={() => setModalIdx(null)} className="text-sm font-semibold text-text-primary hover:text-petrol-600 transition-colors">Close</button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   COVERAGE BAND (replaces empty logo wall)
   ═══════════════════════════════════════════════════ */

function CoverageBand() {
  const stats = [
    { value: "12,500+", label: "Enriched investor contacts" },
    { value: "2,800+", label: "Funds covered globally" },
    { value: "6", label: "Enrichment dimensions per lead" },
    { value: "Weekly", label: "Data refresh cadence" },
  ] as const;

  return (
    <Section>
      <div className="bg-charcoal-900 rounded-card p-8 md:p-12 relative overflow-hidden">
        <HoneycombPattern opacity={0.04} className="text-honey-500" />
        <div className="relative">
          <div className="text-center mb-10">
            <p className="text-xs font-semibold uppercase tracking-widest text-honey-500/70 mb-2">Coverage</p>
            <h3 className="text-[24px] font-[650] text-charcoal-text">Seed to growth. Global. Partner-level.</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-2xl md:text-3xl font-[700] text-honey-500 mb-1">{s.value}</div>
                <div className="text-xs text-charcoal-text/50 uppercase tracking-wider">{s.label}</div>
              </div>
            ))}
          </div>
          <div className="mt-8 pt-6 border-t border-charcoal-border">
            <div className="flex items-center justify-center gap-2">
              <MicroProof testimonial={TESTIMONIALS[2]} className="max-w-2xl bg-charcoal-800 border-charcoal-border [&_blockquote]:text-charcoal-text/70 [&_div]:text-charcoal-text [&_div]:text-charcoal-text/50" />
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   PRICING
   ═══════════════════════════════════════════════════ */

function Pricing() {
  return (
    <Section id="pricing" className="relative bg-surface-warm border-y border-border-subtle overflow-hidden">
      <HoneycombPattern opacity={0.035} className="text-text-primary" />
      <div className="relative">
        <SectionTitle subtitle="Simple pricing, no lock-in. Start small or go deep.">Pricing</SectionTitle>
        <div className="grid md:grid-cols-3 gap-0 md:gap-0 items-stretch">
          {PRICING_TIERS.map((tier, i) => {
            const isMiddle = tier.highlighted;
            return (
              <div key={tier.name} className={`relative flex flex-col bg-surface-primary p-7 ${isMiddle ? "md:scale-[1.03] md:z-10 border-2 border-honey-500/40 shadow-honey-glow rounded-card" : `border border-border-subtle shadow-card ${i === 0 ? "rounded-t-card md:rounded-l-card md:rounded-tr-none" : "rounded-b-card md:rounded-r-card md:rounded-bl-none"}`}`}>
                {isMiddle && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-honey-500 text-charcoal-900 text-[11px] font-semibold px-3 py-1 rounded-full shadow-sm">Recommended</span>
                  </div>
                )}
                <div className="mb-4 pb-4 border-b border-border-subtle">
                  <h3 className="text-lg font-semibold text-text-primary">{tier.name}</h3>
                  <p className="text-sm text-text-secondary mt-1">{tier.description}</p>
                </div>
                <div className="mb-6">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-1">Price</p>
                  <span className="text-3xl font-[700] text-text-primary">{tier.price}</span>
                  <span className="text-sm text-text-muted ml-1">{tier.period}</span>
                </div>
                <ul className="space-y-2.5 mb-8 flex-1">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2">
                      <Check size={14} strokeWidth={2} className="text-honey-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-text-secondary">{f}</span>
                    </li>
                  ))}
                </ul>
                {isMiddle ? (
                  <ButtonPrimary className="w-full" onClick={scrollToForm}>{tier.cta}</ButtonPrimary>
                ) : (
                  <ButtonSecondary className="w-full" onClick={scrollToForm}>{tier.cta}</ButtonSecondary>
                )}
              </div>
            );
          })}
        </div>

        {/* Comparison table */}
        <div className="mt-12 overflow-x-auto -mx-6 px-6">
          <table className="w-full min-w-[600px] text-sm">
            <thead>
              <tr className="border-b border-border-subtle">
                <th className="text-left py-3 pr-4 text-text-secondary font-medium">Feature</th>
                <th className="text-center py-3 px-4 text-text-primary font-semibold">Starter</th>
                <th className="text-center py-3 px-4 text-text-primary font-semibold"><span className="inline-flex items-center gap-1">Growth <span className="w-1.5 h-1.5 rounded-full bg-honey-500" /></span></th>
                <th className="text-center py-3 pl-4 text-text-primary font-semibold">Scale</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr key={row.feature} className="border-b border-border-subtle/60">
                  <td className="py-3 pr-4 text-text-secondary font-medium"><span className="inline-flex items-center">{row.feature}{"tooltip" in row && row.tooltip && <TooltipInline text={row.tooltip} />}</span></td>
                  {(["starter", "growth", "scale"] as const).map((t) => {
                    const val = row[t];
                    return (
                      <td key={t} className="text-center py-3 px-4">
                        {typeof val === "boolean" ? (val ? <Check size={16} strokeWidth={2} className="text-honey-500 mx-auto" /> : <span className="text-text-muted">--</span>) : <span className="text-text-secondary text-sm">{val}</span>}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   FAQ
   ═══════════════════════════════════════════════════ */

function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-border-subtle last:border-0">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between py-5 text-left group" aria-expanded={open}>
        <span className="text-[15px] font-semibold text-text-primary group-hover:text-petrol-600 transition-colors pr-4">{question}</span>
        {open ? <ChevronUp size={18} strokeWidth={1.75} className="text-text-muted flex-shrink-0" /> : <ChevronDown size={18} strokeWidth={1.75} className="text-text-muted flex-shrink-0" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
            <p className="pb-5 text-sm text-text-secondary leading-relaxed pr-8">{answer}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function FAQAccordion() {
  return (
    <Section id="faq">
      <SectionTitle subtitle="Common questions about the data, process, and deliverables.">Frequently asked questions</SectionTitle>
      <div className="max-w-2xl">
        <Card hover={false}>{FAQS.map((faq) => <FAQItem key={faq.question} question={faq.question} answer={faq.answer} />)}</Card>
      </div>
    </Section>
  );
}

/* ═══════════════════════════════════════════════════
   FINAL CTA + FOOTER
   ═══════════════════════════════════════════════════ */

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function FinalCTAForm() {
  const [form, setForm] = useState<FormState>({ email: "", name: "", company: "", stage: "", sector: "", raising90Days: false });
  const [submitted, setSubmitted] = useState(false);
  const canSubmit = isValidEmail(form.email);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitted(true);
  }

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <Section id="final-cta" className="bg-charcoal-900 border-t border-charcoal-border">
      <div className="max-w-xl mx-auto text-center">
        <h2 className="text-[28px] md:text-[32px] leading-[1.2] font-[650] text-charcoal-text mb-3">Get your thesis-fit target list</h2>
        <p className="text-sm text-charcoal-text/50 mb-10">Tell us about your raise. We&apos;ll build your first target list within 48 hours.</p>
        {submitted ? (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-white/[0.06] backdrop-blur-xl rounded-glass border border-white/10 p-8">
            <div className="w-14 h-14 rounded-full bg-honey-500/20 flex items-center justify-center mx-auto mb-4"><Check size={28} strokeWidth={2} className="text-honey-500" /></div>
            <h3 className="text-xl font-semibold text-charcoal-text mb-2">You&apos;re in.</h3>
            <p className="text-sm text-charcoal-text/50">We&apos;ll reach out within 48 hours with your first target list and next steps.</p>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="text-left space-y-4">
            <div className="bg-white/[0.04] backdrop-blur-xl rounded-glass border border-white/10 p-6 space-y-4">
              <Input label="Email" id="email" type="email" required value={form.email} onChange={(v) => update("email", v)} placeholder="you@company.com" />
              <div className="grid sm:grid-cols-2 gap-4">
                <Input label="Name" id="name" value={form.name} onChange={(v) => update("name", v)} placeholder="Optional" />
                <Input label="Company" id="company" value={form.company} onChange={(v) => update("company", v)} placeholder="Optional" />
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                <Select label="Stage" id="stage" value={form.stage} onChange={(v) => update("stage", v as Stage)} options={STAGES} placeholder="Select stage..." />
                <Select label="Sector" id="sector" value={form.sector} onChange={(v) => update("sector", v as Sector)} options={SECTORS} placeholder="Select sector..." />
              </div>
              <label className="flex items-center gap-2.5 cursor-pointer pt-1">
                <input type="checkbox" checked={form.raising90Days} onChange={(e) => update("raising90Days", e.target.checked)} className="w-4 h-4 rounded border-border-strong text-honey-500 focus:ring-honey-glow" aria-label="Raising in the next 90 days" />
                <span className="text-sm text-text-secondary">I&apos;m raising in the next 90 days</span>
              </label>
            </div>
            <ButtonPrimary type="submit" disabled={!canSubmit} className="w-full py-3.5 text-base">Request access</ButtonPrimary>
            {/* Near-CTA proof */}
            <div className="pt-2">
              <p className="text-center text-xs text-charcoal-text/30 mb-3">Trusted by founders at every stage</p>
              <div className="flex items-center justify-center gap-4">
                {TESTIMONIALS.slice(0, 3).map((t) => (
                  <div key={t.name} className="flex items-center gap-1.5">
                    <AvatarPlaceholder size={20} />
                    <span className="text-[10px] text-charcoal-text/40">{t.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </form>
        )}
      </div>
    </Section>
  );
}

function Footer() {
  return (
    <footer className="bg-charcoal-900 border-t border-charcoal-border py-8">
      <Container>
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <a href="#" className="flex items-center gap-1.5 text-charcoal-text/50 hover:text-charcoal-text/70 transition-colors">
              <HoneypotMark size={12} className="text-charcoal-text/40" /><span className="text-xs font-semibold">Honeypot</span>
            </a>
            <a href="mailto:hello@honeypot.vc" className="text-charcoal-text/40 hover:text-charcoal-text/60 text-xs transition-colors">hello@honeypot.vc</a>
            <a href="#" aria-label="LinkedIn" className="text-charcoal-text/40 hover:text-charcoal-text/60 transition-colors"><Linkedin size={14} strokeWidth={1.75} /></a>
            <a href="#" className="text-charcoal-text/40 hover:text-charcoal-text/60 text-xs transition-colors">Privacy Policy</a>
          </div>
          <p className="text-charcoal-text/25 text-[11px] text-center md:text-right max-w-md">We provide research and advisory support; we do not guarantee fundraising outcomes.</p>
        </div>
      </Container>
    </footer>
  );
}

/* ═══════════════════════════════════════════════════
   PAGE
   ═══════════════════════════════════════════════════ */

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <HeroProofStrip />
        <ProblemSolutionBand />
        <HowItWorks />
        <WhatYouGet />
        <FeatureDeepDive />
        <Proof />
        <CaseStudyCarousel />
        <CoverageBand />
        <Pricing />
        <FAQAccordion />
        <FinalCTAForm />
      </main>
      <Footer />
    </>
  );
}
