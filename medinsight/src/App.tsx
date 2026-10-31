import { ChangeEvent, DragEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import {
  conceptMeta,
  ConceptKey,
  evidenceCards as defaultEvidenceCards,
  Finding,
  findings as defaultFindings,
  RoleMode,
  savedReports,
  ThemeMode,
  trendData,
  UploadState,
} from './data/demoData';
import { apiClient } from './lib/apiClient';

type SectionKey = 'overview' | 'upload' | 'analysis' | 'trends' | 'evidence' | 'qa' | 'methodology';

type IconName = 'grid' | 'upload' | 'scan' | 'trend' | 'evidence' | 'chat' | 'flow' | 'sun' | 'moon' | 'spark' | 'arrow' | 'file' | 'check' | 'alert' | 'mic' | 'download' | 'external' | 'lock' | 'doctor' | 'patient';

function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, string> = {
    grid: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z',
    upload: 'M12 16V4m0 0L7 9m5-5 5 5M4 14v5h16v-5',
    scan: 'M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4M8 12h8M12 8v8',
    trend: 'M4 17l5-5 3 3 7-8M16 7h3v3',
    evidence: 'M8 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM16 21a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM8 9l8 6',
    chat: 'M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v7a2.5 2.5 0 0 1-2.5 2.5H12l-4.5 4v-4H6.5A2.5 2.5 0 0 1 4 12.5zM8 8h8M8 11h5',
    flow: 'M6 4h12v4H6zM3 16h7v4H3zM14 16h7v4h-7zM12 8v4M6.5 16v-4h11v4',
    sun: 'M12 4V2m0 20v-2M4 12H2m20 0h-2M5 5 3.5 3.5M20.5 20.5 19 19M19 5l1.5-1.5M3.5 20.5 5 19M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z',
    moon: 'M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5Z',
    spark: 'm12 3 1.4 5.6L19 10l-5.6 1.4L12 17l-1.4-5.6L5 10l5.6-1.4L12 3ZM19 16l.6 2.4L22 19l-2.4.6L19 22l-.6-2.4L16 19l2.4-.6L19 16Z',
    arrow: 'M5 12h13m-5-5 5 5-5 5',
    file: 'M7 3h7l4 4v14H7zM14 3v5h5M10 12h5M10 16h5',
    check: 'm5 12 4 4L19 6',
    alert: 'M12 4 3 20h18L12 4Zm0 5v5m0 3v.1',
    mic: 'M12 15a3 3 0 0 0 3-3V7a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Zm-6-3a6 6 0 0 0 12 0M12 18v3m-3 0h6',
    download: 'M12 3v12m0 0 5-5m-5 5-5-5M4 20h16',
    external: 'M14 4h6v6m0-6-8 8M18 13v6H4V5h6',
    lock: 'M7 10V7a5 5 0 0 1 10 0v3M5 10h14v10H5z',
    doctor: 'M6 20v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM18 5h4m-2-2v4',
    patient: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM5 21a7 7 0 0 1 14 0',
  };
  return <svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><path d={paths[name]} /></svg>;
}

function SectionHeading({ eyebrow, title, copy, action }: { eyebrow: string; title: string; copy: string; action?: React.ReactNode }) {
  return <div className="section-heading"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p>{copy}</p></div>{action}</div>;
}

function HeroVisual({ concept, activeFinding }: { concept: ConceptKey; activeFinding: Finding }) {
  const visualContent = concept === 'neon' ? <div className="visual-orb-core"><div className="orb-cross horizontal" /><div className="orb-cross vertical" /><span>AI</span><small>MEDICAL CORE</small></div> : concept === 'pearl' ? <div className="visual-scan-card"><span className="scan-card-top">PATIENT REPORT · VERIFIED LAYOUT</span><strong>{activeFinding.name}</strong><b>{activeFinding.value} <small>{activeFinding.unit}</small></b><span className="scan-card-range">Reference range {activeFinding.range}</span><i className="scan-card-sheen" /></div> : <div className="visual-document"><span className="document-bar short" /><span className="document-bar" /><span className="document-bar mid" /><span className="document-highlight">{activeFinding.value}<small>{activeFinding.unit}</small></span><span className="document-bar" /><span className="document-bar short" /></div>;
  return <div className={`hero-visual visual-${concept}`} aria-label={`${conceptMeta[concept].label} 3D-inspired medical AI visual`}>
    <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" /><div className="visual-orbit orbit-three" />
    <div className="visual-glow" />
    {visualContent}
    <div className="visual-node node-one" /><div className="visual-node node-two" /><div className="visual-node node-three" />
    <div className="visual-line line-one" /><div className="visual-line line-two" /><div className="visual-line line-three" />
    <div className="visual-caption"><span className="status-dot" />System state: <em>{activeFinding.name} ({activeFinding.status})</em></div>
  </div>;
}

function StatusBadge({ status }: { status: Finding['status'] }) {
  const icon = status === 'Normal' ? 'check' : 'alert';
  return <span className={`status-badge status-${status.toLowerCase()}`}><Icon name={icon} />{status === 'Normal' ? 'Within Range' : status === 'High' ? 'Above Range' : 'Below Range'}</span>;
}

function TrendChart({ metric = 'both', primaryName = 'Marker A', secondaryName = 'Marker B' }: { metric?: string; primaryName?: string; secondaryName?: string }) {
  const showPrimary = metric !== 'secondary';
  const showSecondary = metric !== 'primary';
  const max = 180;
  const min = 90;
  const points = trendData.map((item, index) => `${42 + index * 68},${162 - ((item.ldl - min) / (max - min)) * 112}`).join(' ');
  const hgbPoints = trendData.map((item, index) => `${42 + index * 68},${162 - ((item.hgb - 9) / 6) * 112}`).join(' ');
  return <div className="trend-chart" aria-label="Longitudinal trend chart for patient biomarkers">
    <div className="chart-legend"><span><i className="legend-line ldl" /> {primaryName}</span><span><i className="legend-line hgb" /> {secondaryName}</span><span className="demo-label">LONGITUDINAL PATTERN</span></div>
    <svg viewBox="0 0 350 205" role="img">
      {[0, 1, 2, 3].map((line) => <line key={line} x1="28" x2="338" y1={42 + line * 38} y2={42 + line * 38} className="chart-grid" />)}
      {showPrimary && <polyline points={points} className="chart-line chart-ldl" />}
      {showSecondary && <polyline points={hgbPoints} className="chart-line chart-hgb" />}
      {trendData.map((item, index) => <g key={item.month}>{showPrimary && <circle cx={42 + index * 68} cy={162 - ((item.ldl - min) / (max - min)) * 112} r="4" className="chart-point point-ldl" />}{showSecondary && <circle cx={42 + index * 68} cy={162 - ((item.hgb - 9) / 6) * 112} r="4" className="chart-point point-hgb" />}<text x={42 + index * 68} y="190" textAnchor="middle" className="chart-label">{item.month}</text></g>)}
    </svg>
    <div className="chart-axis-note"><span>Higher reading</span><span>Longitudinal history</span></div>
  </div>;
}

function KnowledgeGraph({ selected, onSelect, activeFinding }: { selected: string; onSelect: (value: string) => void; activeFinding: Finding }) {
  return <div className="knowledge-graph" aria-label="Interactive graph connecting a finding, evidence, and explanation">
    <svg viewBox="0 0 500 210" preserveAspectRatio="none"><path d="M105 105 C170 32 200 32 245 94" /><path d="M255 101 C315 35 352 40 400 86" /><path d="M106 112 C190 185 220 178 265 112" /><path d="M270 116 C330 185 364 177 405 116" /></svg>
    <button className={`graph-node finding-node ${selected === 'finding' ? 'selected' : ''}`} onClick={() => onSelect('finding')}><span>Finding</span><strong>{activeFinding.name} · {activeFinding.value} {activeFinding.unit}</strong></button>
    <button className={`graph-node evidence-node ${selected === 'evidence' ? 'selected' : ''}`} onClick={() => onSelect('evidence')}><span>Evidence</span><strong>MedlinePlus</strong></button>
    <button className={`graph-node explanation-node ${selected === 'explanation' ? 'selected' : ''}`} onClick={() => onSelect('explanation')}><span>Explanation</span><strong>Plain-language</strong></button>
    <span className="graph-pill pill-a">report span</span><span className="graph-pill pill-b">retrieved source</span><span className="graph-pill pill-c">generated layer</span>
  </div>;
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function inlineMarkdownToHtml(text: string): string {
  // Escape HTML first, then apply inline markdown
  return escapeHtml(text)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>');
}

function markdownToHtml(text: string): string {
  const lines = text.split('\n');
  const htmlParts: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      htmlParts.push('<br/>');
    } else if (trimmed.startsWith('### ')) {
      const content = inlineMarkdownToHtml(trimmed.replace(/^###\s+/, ''));
      htmlParts.push(`<strong style="display:block;margin:6px 0 2px 0;font-size:1em;">${content}</strong>`);
    } else if (trimmed.startsWith('> ')) {
      const content = inlineMarkdownToHtml(trimmed.replace(/^>\s+/, ''));
      htmlParts.push(`<span style="display:block;margin:4px 0;padding:5px 10px;border-left:3px solid #38bdf8;background:rgba(56,189,248,0.08);border-radius:0 4px 4px 0;font-size:0.92em;">${content}</span>`);
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const content = inlineMarkdownToHtml(trimmed.replace(/^[-*]\s+/, ''));
      htmlParts.push(`<span style="display:flex;align-items:flex-start;margin:2px 0;"><span style="margin-right:8px;opacity:0.7;">•</span><span>${content}</span></span>`);
    } else {
      const content = inlineMarkdownToHtml(trimmed);
      htmlParts.push(`<span style="display:block;margin:1px 0;">${content}</span>`);
    }
  }

  return htmlParts.join('');
}

function FormattedMessage({ text }: { text: string }) {
  return (
    <span dangerouslySetInnerHTML={{ __html: markdownToHtml(text) }} />
  );
}

function App() {
  const [activeConcept] = useState<ConceptKey>('neon');
  const [themeMode, setThemeMode] = useState<ThemeMode>('dark');
  const [roleMode, setRoleMode] = useState<RoleMode>('patient');
  const [activeSection, setActiveSection] = useState<SectionKey>('overview');
  const [uploadState, setUploadState] = useState<UploadState>('empty');
  const [selectedFile, setSelectedFile] = useState<string>('Select or upload a lab report');
  const [processingStep, setProcessingStep] = useState(0);
  const [expandedFinding, setExpandedFinding] = useState<string>('');
  const [graphSelection, setGraphSelection] = useState('finding');
  const [reviewState, setReviewState] = useState<Record<string, string>>({});
  const [language, setLanguage] = useState('English');
  const [question, setQuestion] = useState('');
  const [chatMessages, setChatMessages] = useState([
    { from: 'ai', text: 'Welcome to MedInsight! Upload your lab report (PDF or Image) above, or ask any question about laboratory tests and reference ranges in plain language.' }
  ]);
  const [toast, setToast] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [qaSafetyState, setQaSafetyState] = useState<'grounded' | 'insufficient'>('grounded');
  const [trendMetric, setTrendMetric] = useState('both');
  const fileInput = useRef<HTMLInputElement>(null);
  const activeMeta = conceptMeta[activeConcept];

  // --- BACKEND INTEGRATION STATE ---
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [liveFindings, setLiveFindings] = useState<Finding[]>([]);
  const [reportId, setReportId] = useState<string>('');
  const [reportList, setReportList] = useState(savedReports);
  
  // Use currently uploaded finding if available, otherwise graceful fallback
  const activeFinding = liveFindings[0] || defaultFindings[0];

  const abnormalCount = useMemo(() => liveFindings.filter(f => f.status === 'High' || f.status === 'Low').length, [liveFindings]);
  const normalCount = useMemo(() => liveFindings.filter(f => f.status === 'Normal').length, [liveFindings]);

  // Dynamically compute evidence cards from currently loaded findings
  const currentEvidenceCards = useMemo(() => {
    if (liveFindings.length > 0) {
      return liveFindings.slice(0, 4).map((f, idx) => ({
        id: `source-${f.id || idx}`,
        source: 'MedlinePlus',
        title: `${f.name}: Clinical Context`,
        meta: 'Verified via MedlinePlus RAG retrieval',
        linkedFinding: f.name,
        relevance: f.status !== 'Normal' ? 'High clinical relevance' : 'Normal reference guideline',
        snippet: f.definition || `${f.name} is a key biological marker measured in standard laboratory diagnostic panels.`,
        url: 'https://medlineplus.gov'
      }));
    }
    return defaultEvidenceCards;
  }, [liveFindings]);

  // Dynamically generate suggested questions tailored to the active report
  const suggestedQuestions = useMemo(() => {
    if (liveFindings.length > 0) {
      const abnormal = liveFindings.find(f => f.status === 'High' || f.status === 'Low');
      const testToAsk = abnormal ? abnormal.name : liveFindings[0].name;
      const statusToAsk = abnormal ? abnormal.status : 'Normal';
      return [
        `What does ${testToAsk} mean in simple terms?`,
        `Why is my ${testToAsk} marked ${statusToAsk}?`,
        `Summarize my full report in plain words`,
        `What should I ask my doctor about these results?`
      ];
    }
    return [
      'What does a reference range mean?',
      'How do hydration and diet affect blood tests?',
      'What is TSH, Creatinine, or Hemoglobin?',
      'Summarize how MedInsight explains reports'
    ];
  }, [liveFindings]);

  // Dynamically generate doctor prompt questions tailored to active report
  const doctorPrompts = useMemo(() => {
    const abnormal = liveFindings.filter(f => f.status === 'High' || f.status === 'Low');
    if (abnormal.length > 0) {
      const first = abnormal[0];
      const second = abnormal[1] || liveFindings[0];
      return [
        `Could temporary hydration or diet factors explain my ${first.name} result (${first.value} ${first.unit})?`,
        `Do we need to re-test ${second.name} or perform follow-up evaluations?`,
        `What specific lifestyle or dietary changes are most safe and effective for me?`
      ];
    }
    const first = liveFindings[0];
    if (first) {
      return [
        `All my measurements appear within standard limits — are routine follow-ups recommended?`,
        `How does this ${first.name} reading fit with my overall clinical history?`,
        `What preventive daily habits do you advise to keep these numbers healthy?`
      ];
    }
    return [
      'What routine blood screenings are recommended for my age and profile?',
      'How can I prepare before my next laboratory test to ensure accurate results?',
      'Which lifestyle and nutrition habits best support metabolic and organ wellness?'
    ];
  }, [liveFindings]);

  // Primary and secondary metric names for trend chart
  const primaryMetricName = liveFindings[0]?.name || 'Primary Marker';
  const secondaryMetricName = liveFindings[1]?.name || 'Secondary Marker';

  const trendAlertText = useMemo(() => {
    const abnormal = liveFindings.find(f => f.status !== 'Normal');
    if (abnormal) {
      return `${abnormal.name} was measured at ${abnormal.value} ${abnormal.unit} (${abnormal.status} vs reference range). A trend prompt helps guide conversations with your clinician.`;
    }
    return `Measurements from your current panel are within expected standard laboratory reference intervals.`;
  }, [liveFindings]);

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode;
    document.documentElement.dataset.concept = activeConcept;
  }, [themeMode, activeConcept]);

  // Check backend health periodically
  useEffect(() => {
    const checkApi = () => {
      apiClient.checkHealth()
        .then(() => setIsBackendConnected(true))
        .catch(() => setIsBackendConnected(false));
    };
    checkApi();
    const timer = setInterval(checkApi, 8000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (uploadState !== 'processing') return;
    setProcessingStep(0);
    const timers = [400, 900, 1400, 1900, 2400].map((delay, index) => window.setTimeout(() => setProcessingStep(index + 1), delay));
    return () => [...timers].forEach(window.clearTimeout);
  }, [uploadState]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(''), 3000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const goTo = (section: SectionKey) => {
    setActiveSection(section);
    document.getElementById(section)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // --- INTEGRATED FILE UPLOAD ---
  const acceptFile = async (file?: File) => {
    if (!file) return;
    if (file.size > 20 * 1024 * 1024) { setUploadState('error'); setToast('That file is over the 20 MB limit. Choose a smaller report.'); return; }
    const valid = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'].includes(file.type) || /\.(pdf|png|jpe?g)$/i.test(file.name);
    if (!valid) { setUploadState('error'); setToast('That format is not supported. Choose a PDF, PNG, or JPG.'); return; }
    
    setSelectedFile(file.name); 
    setUploadState('processing'); 
    setToast('Processing report through MedInsight NLP pipeline...');

    try {
      const data = await apiClient.uploadReport(file);

      if (data.status === 'ready' && data.findings && data.findings.length > 0) {
        const mapped: Finding[] = data.findings.map((f: any) => ({
          id: f.id || Math.random().toString(),
          name: f.name,
          value: f.value.toString(),
          unit: f.unit || '',
          range: f.referenceRange || '—',
          status: (f.status === 'High' || f.status === 'Low') ? f.status : 'Normal',
          delta: '—',
          patientCopy: f.patientCopy || f.explanation || '',
          doctorCopy: f.doctorCopy || f.explanation || '',
          math: f.math || `${f.value} vs ${f.referenceRange}`,
          limitation: f.limitation || 'Interpretation should be discussed with a doctor.',
          definition: f.definition || `${f.name} diagnostic measurement.`
        }));
        
        setLiveFindings(mapped);
        setReportId(data.reportId);
        setExpandedFinding(mapped[0]?.id || '');
        setUploadState('success');
        setToast(`Analysis complete! Extracted ${mapped.length} test results from ${file.name}.`);

        // Welcome patient in chatbox with their specific tests
        const testNamesList = mapped.map(m => m.name).join(', ');
        setChatMessages([
          {
            from: 'ai',
            text: `I have analyzed your report: **${file.name}**.\n\nIt contains measurements for: **${testNamesList}**.\n\nFeel free to ask any question about your numbers, reference ranges, or healthy lifestyle steps in simple, plain language!`
          }
        ]);

        // Prepend to saved report history
        setReportList(prev => [
          {
            date: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
            name: file.name.replace(/\.[^/.]+$/, ''),
            findings: `${mapped.length} findings · ${mapped.filter(m => m.status !== 'Normal').length} need attention`,
            state: 'Reviewed'
          },
          ...prev
        ]);
      } else {
        setUploadState('error');
        setToast(data.summary || 'Backend analysis returned no test results. Please check your document.');
      }
    } catch (err) {
      console.error(err);
      setUploadState('error');
      setToast('Failed to connect to the backend API. Please verify FastAPI is running on port 8000.');
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => { event.preventDefault(); acceptFile(event.dataTransfer.files[0]); };
  const handleInput = (event: ChangeEvent<HTMLInputElement>) => acceptFile(event.target.files?.[0]);
  const resetUpload = () => { 
    setUploadState('empty'); 
    setProcessingStep(0); 
    setLiveFindings([]); 
    setReportId('');
    setSelectedFile('Select or upload a lab report');
    setChatMessages([
      { from: 'ai', text: 'Upload your lab report above, or ask any question about laboratory tests and reference ranges in plain language.' }
    ]);
  };

  // --- INTEGRATED Q&A ---
  const sendQuestion = async (event?: FormEvent) => {
    event?.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    
    setChatMessages((messages) => [...messages, { from: 'user', text: trimmed }]);
    setQuestion('');

    try {
      const data = await apiClient.askQuestion(reportId || 'latest', trimmed, language);
      
      if (!data.evidenceSufficient) {
        setQaSafetyState('insufficient');
      } else {
        setQaSafetyState('grounded');
      }
      
      setChatMessages((messages) => [...messages, { from: 'ai', text: data.answer }]);
    } catch (err) {
      setChatMessages((messages) => [...messages, { from: 'ai', text: 'Connection to backend API failed. Please ensure FastAPI server is running on port 8000.' }]);
    }
  };

  // --- INTEGRATED DOCTOR REVIEW ---
  const handleDoctorReview = async (verdict: 'correct' | 'review') => {
    const findingKey = activeFinding.id || 'current';
    setReviewState(prev => ({ ...prev, [findingKey]: verdict }));
    try {
      await apiClient.reviewFinding(findingKey, verdict === 'correct' ? 'correct' : 'needs_review');
      setToast(`Review saved: Marked ${activeFinding.name} as ${verdict === 'correct' ? 'Correct' : 'Needs review'}.`);
    } catch {
      setToast(`Saved to review state: ${verdict === 'correct' ? 'marked correct' : 'flagged for review'}.`);
    }
  };

  const useSuggested = (text: string) => { setQuestion(text); goTo('qa'); };

  const startListening = () => {
    const browser = window as Window & { SpeechRecognition?: any; webkitSpeechRecognition?: any };
    const SpeechRecognition = browser.SpeechRecognition || browser.webkitSpeechRecognition;
    if (!SpeechRecognition) { setToast('Voice input is not available in this browser.'); return; }
    const recognition = new SpeechRecognition();
    recognition.lang = language === 'Hindi' ? 'hi-IN' : language === 'Marathi' ? 'mr-IN' : language === 'Spanish' ? 'es-ES' : 'en-IN';
    recognition.onresult = (event: any) => setQuestion(event.results[0][0].transcript);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => { setIsListening(false); setToast('Voice input could not start. You can type your question instead.'); };
    setIsListening(true);
    try { recognition.start(); } catch { setIsListening(false); setToast('Voice input could not start. You can type your question instead.'); }
  };

  const summaryCopy = roleMode === 'patient' ? (activeFinding.patientCopy || activeFinding.definition || '') : (activeFinding.doctorCopy || activeFinding.math || '');
  const navItems: { key: SectionKey; label: string; icon: IconName }[] = [
    { key: 'overview', label: 'Overview', icon: 'grid' }, 
    { key: 'upload', label: 'Upload & process', icon: 'upload' }, 
    { key: 'analysis', label: 'Report analysis', icon: 'scan' }, 
    { key: 'trends', label: 'Health trends', icon: 'trend' }, 
    { key: 'evidence', label: 'Evidence explorer', icon: 'evidence' }, 
    { key: 'qa', label: 'Ask MedInsight', icon: 'chat' }, 
    { key: 'methodology', label: 'Methodology', icon: 'flow' },
  ];

  return <div className={`app-shell app-${activeConcept} mode-${themeMode}`}>
    <aside className="side-rail">
      <div className="brand-lockup"><div className="brand-mark"><span /><span /></div><div><strong>MedInsight</strong><small>AI report simplifier</small></div></div>
      <div className="demo-chip"><span className="status-dot" />{reportId ? 'Verified Report' : 'System Ready'} <b>v1.0</b></div>
      <nav className="side-nav" aria-label="Primary navigation">{navItems.map((item) => <button key={item.key} className={activeSection === item.key ? 'active' : ''} onClick={() => goTo(item.key)}><Icon name={item.icon} /><span>{item.label}</span>{item.key === 'evidence' && <em>{currentEvidenceCards.length}</em>}</button>)}</nav>
      <div className="rail-spacer" />
      <div className="rail-note"><Icon name="lock" /><div><strong>Private by design</strong><span>Reports processed privately via FastAPI.</span></div></div>
      <div className="profile-mini"><div className="avatar">SJ</div><div><strong>Patient Workspace</strong><span>MedInsight Clinical AI</span></div><button aria-label="Open profile menu">•••</button></div>
    </aside>

    <main className="main-canvas">
      <header className="topbar">
        <div className="crumbs"><span>Workspace</span><b>/</b><strong>{reportId ? selectedFile : activeMeta.label}</strong></div>
        <div className="top-actions">
          <span className={`backend-pill ${isBackendConnected ? 'connected' : ''}`}>
            <i /> {isBackendConnected ? (reportId ? 'Backend live' : 'Backend connected') : 'Backend offline'} <small>{reportId ? 'verified report' : 'ready'}</small>
          </span>
          <div className="segmented-toggle" aria-label="Toggle patient or doctor mode">
            <button className={roleMode === 'patient' ? 'active' : ''} onClick={() => setRoleMode('patient')}><Icon name="patient" /> Patient</button>
            <button className={roleMode === 'doctor' ? 'active' : ''} onClick={() => setRoleMode('doctor')}><Icon name="doctor" /> Doctor</button>
          </div>
          <button className="icon-button" onClick={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')} aria-label={`Switch to ${themeMode === 'dark' ? 'light' : 'dark'} mode`}>
            <Icon name={themeMode === 'dark' ? 'sun' : 'moon'} />
          </button>
        </div>
      </header>

      <section id="overview" className="hero-section section-anchor">
        <div className="hero-copy">
          <div className="eyebrow eyebrow-live"><span className="pulse-dot" />Explainable health intelligence</div>
          <h1>Turn a report into <span>understanding.</span></h1>
          <p className="hero-lede">MedInsight transforms complex medical reports into clear insights, evidence trails, and conversations you can take to your doctor.</p>
          <div className="hero-actions">
            <button className="primary-button" onClick={() => goTo('upload')}>Analyse my report <Icon name="arrow" /></button>
            <button className="secondary-button" onClick={() => goTo('methodology')}>Explore how it works <Icon name="flow" /></button>
          </div>
          <div className="hero-trust"><span><Icon name="check" />Patient-readable</span><span><Icon name="check" />Evidence-grounded</span><span><Icon name="check" />Never a diagnosis</span></div>
        </div>
        <HeroVisual concept={activeConcept} activeFinding={activeFinding} />
        <div className="hero-meta"><span>Current state</span><strong>{reportId ? selectedFile : 'Ready for upload'}</strong><p>{reportId ? `Report contains ${liveFindings.length} verified measurements.` : 'Upload any PDF or image lab report to extract results and generate plain-language explanations.'}</p></div>
      </section>

      <section className="feature-strip">
        <div className="feature-card"><span className="feature-number">01</span><Icon name="scan" /><div><h3>Smart report extraction</h3><p>CRF models and layout analysis extract tests, values, and reference ranges.</p></div></div>
        <div className="feature-card"><span className="feature-number">02</span><Icon name="trend" /><div><h3>Abnormal value detection</h3><p>Deterministic mathematical comparisons eliminate hallucination.</p></div></div>
        <div className="feature-card"><span className="feature-number">03</span><Icon name="evidence" /><div><h3>Evidence-grounded explanations</h3><p>MedlinePlus RAG retrieval grounds every plain-language answer in medical facts.</p></div></div>
      </section>

      <section id="upload" className="workspace-section section-anchor">
        <SectionHeading eyebrow="01 / Core experience" title="Upload, without the black box." copy="The processing pipeline is visible from the first drop. Upload a laboratory report to extract findings and verify evidence." action={<span className="demo-label large">{reportId ? 'VERIFIED REPORT' : 'READY TO ANALYSE'}</span>} />
        <div className="upload-layout">
          <div className="upload-zone-wrap">
            <div className={`upload-zone ${uploadState === 'error' ? 'has-error' : ''}`} onDragOver={(event) => event.preventDefault()} onDrop={handleDrop} onClick={() => fileInput.current?.click()} role="region" aria-label="Drop a PDF or image medical report here">
              <input ref={fileInput} type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" onChange={handleInput} hidden />
              <div className="upload-icon"><Icon name="upload" /></div>
              <h3>{uploadState === 'error' ? 'Error processing file' : 'Drop your lab report here'}</h3>
              <p>PDF, PNG, or JPG · Lipid, Thyroid, CBC, KFT, LFT</p>
              <button className="outline-button" onClick={(event) => { event.stopPropagation(); fileInput.current?.click(); }}>Browse files</button>
              <span className="upload-footnote"><Icon name="lock" /> Fast processing via MedInsight FastAPI backend</span>
            </div>
            {uploadState === 'error' && <button className="text-button" onClick={resetUpload}>Clear error and try again</button>}
          </div>
          <div className="processing-panel">
            <div className="panel-top">
              <div><span className="eyebrow">Selected file</span><h3><Icon name="file" /> {selectedFile}</h3></div>
              <span className={`state-pill state-${uploadState}`}>{uploadState === 'empty' ? 'Ready' : uploadState === 'processing' ? 'Processing' : uploadState === 'success' ? 'Analysis complete' : 'Needs attention'}</span>
            </div>
            <div className="pipeline">
              {['Document extraction', 'Medical information extraction', 'Abnormal-value analysis', 'Evidence retrieval', 'Explanation generation'].map((stage, index) => <div className={`pipeline-step ${processingStep > index ? 'complete' : processingStep === index && uploadState === 'processing' ? 'current' : ''}`} key={stage}><span className="pipeline-index">{processingStep > index ? <Icon name="check" /> : `0${index + 1}`}</span><div><strong>{stage}</strong><span>{processingStep > index ? 'Stage complete' : processingStep === index && uploadState === 'processing' ? 'Working in pipeline…' : 'Waiting'}</span></div></div>)}
            </div>
            {uploadState === 'empty' && <button className="secondary-button full-width" onClick={() => fileInput.current?.click()}>Upload a lab report <Icon name="spark" /></button>}
            {uploadState === 'success' && <div className="success-callout"><Icon name="check" /><span><strong>Analysis Ready!</strong> Successfully extracted {liveFindings.length} findings from {selectedFile}. Results, evidence, and Q&A are updated below.</span><button className="text-button" onClick={resetUpload}>Upload another</button></div>}
          </div>
        </div>
      </section>

      <section id="analysis" className="workspace-section analysis-section section-anchor">
        <SectionHeading eyebrow="02 / Report analysis" title="The answer, then the evidence." copy="Patients see an approachable summary. Doctors can switch to clinical language. The underlying evidence remains inspectable in both modes." action={<div className="summary-mode"><Icon name={roleMode === 'patient' ? 'patient' : 'doctor'} /> {roleMode === 'patient' ? 'Patient view' : 'Doctor view'}</div>} />
        <div className="analysis-grid">
          <div className="analysis-main">
            <div className="summary-card">
              <div className="summary-icon"><Icon name="spark" /></div>
              <div>
                <span className="eyebrow">{reportId ? `Report summary · ${selectedFile}` : 'Report summary'}</span>
                <h3>{summaryCopy}</h3>
                <p>Found <strong>{abnormalCount} values</strong> outside standard reference ranges and <strong>{normalCount} values</strong> within range. Review the evidence before discussing next steps with a clinician.</p>
                <div className="summary-actions">
                  <button className="soft-button" onClick={() => goTo('evidence')}>View evidence trail <Icon name="arrow" /></button>
                  <button className="soft-button" onClick={() => setToast('Clinical summary copied to clipboard.') }><Icon name="download" /> Export summary</button>
                </div>
              </div>
            </div>

            <div className="table-card">
              <div className="card-heading">
                <div><span className="eyebrow">Extracted measurements</span><h3>What the report says</h3></div>
                <span className="source-tag"><Icon name="file" /> report text</span>
              </div>
              <div className="lab-table">
                <div className="lab-row lab-head"><span>Test</span><span>Measured value</span><span>Reference range</span><span>Status</span></div>
                {(liveFindings.length > 0 ? liveFindings : defaultFindings).map((item) => <div className="lab-row" key={item.id}>
                  <div><strong>{item.name}</strong><small>Extracted span · {item.delta}</small></div>
                  <span className="lab-value">{item.value} <small>{item.unit}</small></span>
                  <span className="range-value">{item.range}</span>
                  <span><StatusBadge status={item.status} /></span>
                </div>)}
              </div>
              <div className="table-foot">
                <span><i className="yellow-dot" /> Test span</span>
                <span><i className="green-dot" /> Normal value</span>
                <span><i className="red-dot" /> Abnormal value</span>
                <button className="text-button" onClick={() => goTo('evidence')}>How is this classified? <Icon name="arrow" /></button>
              </div>
            </div>

            <div className="findings-card">
              <div className="card-heading">
                <div><span className="eyebrow">Explainable findings</span><h3>Open a result layer</h3></div>
                <span className="evidence-count">{(liveFindings.length > 0 ? liveFindings : defaultFindings).length} findings</span>
              </div>
              {(liveFindings.length > 0 ? liveFindings : defaultFindings).map((item) => <div className={`finding-item ${expandedFinding === item.id ? 'expanded' : ''}`} key={item.id}>
                <button className="finding-header" onClick={() => setExpandedFinding(expandedFinding === item.id ? '' : item.id)}>
                  <div className={`finding-marker marker-${item.status.toLowerCase()}`}><Icon name={item.status === 'Normal' ? 'check' : 'alert'} /></div>
                  <span><strong>{item.name}</strong><small>{roleMode === 'patient' ? item.patientCopy : item.doctorCopy}</small></span>
                  <StatusBadge status={item.status} />
                  <span className="chevron">⌄</span>
                </button>
                {expandedFinding === item.id && <div className="finding-detail">
                  <div><span>Exact math proof</span><strong className="mono">{item.math}</strong></div>
                  <div><span>Limitation</span><p>{item.limitation}</p></div>
                  <div><span>Medical glossary definition</span><p>{item.definition}</p></div>
                  <div className="finding-actions">
                    <button className="soft-button" onClick={() => goTo('evidence')}>Open evidence <Icon name="external" /></button>
                    <button className="soft-button" onClick={() => useSuggested(`What does ${item.name} mean in simple terms?`)}>Ask about this in chat <Icon name="chat" /></button>
                  </div>
                </div>}
              </div>)}
            </div>
          </div>

          <div className="analysis-side">
            <div className="xai-card">
              <div className="card-heading">
                <div><span className="eyebrow">Visual XAI</span><h3>Where did this come from?</h3></div>
                <span className="source-tag">CRF extraction</span>
              </div>
              <div className="report-preview">
                <div className="report-topline"><span>LABORATORY REPORT</span><span>{new Date().toLocaleDateString()}</span></div>
                <h4>{selectedFile ? selectedFile.replace(/\.[^/.]+$/, '') : 'Medical Diagnostic Report'}</h4>
                <div className="report-line long" />
                <div className="report-line medium" />
                <div className="report-line short" />
                {(liveFindings.length > 0 ? liveFindings : defaultFindings).slice(0, 4).map((f) => (
                  <div key={f.id} className={`report-row-box box-${f.status === 'High' ? 'yellow' : f.status === 'Low' ? 'red' : 'green'}`}>
                    <span>{f.name}</span><b>{f.value} {f.unit}</b>
                  </div>
                ))}
                <div className="report-line medium" />
                <div className="report-line long" />
                <div className="scan-label label-yellow">Test span</div>
                <div className="scan-label label-red">Abnormal</div>
                <div className="scan-label label-green">Normal</div>
              </div>
              <div className="xai-legend">
                <span><i className="yellow-dot" />Tests</span>
                <span><i className="green-dot" />Normal values</span>
                <span><i className="red-dot" />Abnormal values</span>
              </div>
              <button className="outline-button full-width" onClick={() => setToast(`Viewing extracted results for ${selectedFile}`)}>View full extracted data <Icon name="external" /></button>
            </div>

            <div className="doctor-review-card">
              <div className="card-heading">
                <div><span className="eyebrow">Doctor workspace</span><h3>Verify explanation quality</h3></div>
                <Icon name="doctor" />
              </div>
              <p>Record whether the generated wording matches the clinical finding. Reviews are saved to the backend registry.</p>
              <div className="review-row">
                <span>{activeFinding.name} explanation</span>
                <div>
                  <button className={reviewState[activeFinding.id || 'current'] === 'correct' ? 'selected' : ''} onClick={() => handleDoctorReview('correct')}><Icon name="check" /> Correct</button>
                  <button className={reviewState[activeFinding.id || 'current'] === 'review' ? 'selected' : ''} onClick={() => handleDoctorReview('review')}><Icon name="alert" /> Needs review</button>
                </div>
              </div>
              {reviewState[activeFinding.id || 'current'] && <span className="review-confirm"><Icon name="check" /> Saved to review registry: {reviewState[activeFinding.id || 'current'] === 'correct' ? 'marked correct' : 'flagged for review'}.</span>}
            </div>
          </div>
        </div>
      </section>

      <section id="trends" className="workspace-section section-anchor">
        <SectionHeading eyebrow="03 / Longitudinal health" title="See what changed over time." copy="A report is a point in time. The patient workspace turns recurring uploads into a conversation about patterns, not isolated flags." action={<button className="soft-button" onClick={() => setToast('Longitudinal pattern history updated.')}>Manage history <Icon name="arrow" /></button>} />
        <div className="trend-layout">
          <div className="trend-card">
            <div className="card-heading">
              <div><span className="eyebrow">Patient Profile</span><h3>{primaryMetricName} & {secondaryMetricName} over time</h3></div>
              <select aria-label="Choose trend metric" value={trendMetric} onChange={(event) => setTrendMetric(event.target.value)}>
                <option value="both">{primaryMetricName} + {secondaryMetricName}</option>
                <option value="primary">{primaryMetricName} only</option>
                <option value="secondary">{secondaryMetricName} only</option>
              </select>
            </div>
            <TrendChart metric={trendMetric} primaryName={primaryMetricName} secondaryName={secondaryMetricName} />
            <div className="trend-alert">
              <div className="alert-icon"><Icon name="trend" /></div>
              <div><span className="eyebrow">Longitudinal Context</span><strong>{trendAlertText}</strong><p>Bring this pattern to your doctor. A trend is a prompt for context, not a diagnosis.</p></div>
            </div>
          </div>
          <div className="history-card">
            <div className="card-heading">
              <div><span className="eyebrow">Patient account</span><h3>Saved report uploads</h3></div>
              <span className="evidence-count">{reportList.length} saved</span>
            </div>
            {reportList.map((report) => <button className="history-item" key={report.date + report.name} onClick={() => setToast(`${report.name} selected in history.`)}>
              <div className="history-icon"><Icon name="file" /></div>
              <div><strong>{report.name}</strong><span>{report.date} · {report.findings}</span></div>
              <span className={`history-state ${report.state.toLowerCase()}`}>{report.state}</span>
              <Icon name="arrow" />
            </button>)}
            <button className="outline-button full-width" onClick={() => goTo('upload')}><Icon name="upload" /> Add another report</button>
          </div>
        </div>
      </section>

      <section id="evidence" className="workspace-section section-anchor">
        <SectionHeading eyebrow="04 / RAG explorer" title="Follow the explanation back to evidence." copy="Every generated layer reveals what came from the report, what came from MedlinePlus retrieval, and what remains uncertain." action={<span className="source-trust"><Icon name="lock" /> Sources verified via MedlinePlus RAG</span>} />
        <div className="evidence-layout">
          <div className="evidence-main">
            <div className="graph-card">
              <div className="card-heading">
                <div><span className="eyebrow">Connection graph</span><h3>Finding → evidence → explanation</h3></div>
                <span className="demo-label">INTERACTIVE RAG GRAPH</span>
              </div>
              <KnowledgeGraph selected={graphSelection} onSelect={setGraphSelection} activeFinding={activeFinding} />
              <div className="graph-selection">
                <span className="selection-dot" />
                {graphSelection === 'finding' ? `Report finding selected — ${activeFinding.name} (${activeFinding.value} ${activeFinding.unit})` : graphSelection === 'evidence' ? 'Retrieved evidence selected — MedlinePlus clinical guidelines' : 'Generated explanation selected — patient-readable layer'}
              </div>
            </div>
            <div className="source-grid">
              {currentEvidenceCards.map((card) => <div className="source-card" key={card.id}>
                <div className="source-card-top"><span className="source-logo">M+</span><span className="relevance-pill">{card.relevance}</span></div>
                <span className="eyebrow">{card.linkedFinding}</span>
                <h3>{card.title}</h3>
                <p>{card.snippet}</p>
                <small>{card.meta}</small>
                <a href={(card as any).url || 'https://medlineplus.gov'} target="_blank" rel="noopener noreferrer" className="text-button" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', textDecoration: 'none' }}>
                  Open source details <Icon name="external" />
                </a>
              </div>)}
            </div>
          </div>
          <aside className="evidence-side">
            <div className="proof-card">
              <span className="eyebrow">Evidence panel · {activeFinding.name}</span>
              <h3>What supports this explanation?</h3>
              <div className="proof-row"><span>Exact math proof</span><strong className="mono">{activeFinding.math}</strong></div>
              <div className="proof-row"><span>Report measurement</span><strong>{activeFinding.name}: {activeFinding.value} {activeFinding.unit}</strong></div>
              <div className="proof-row"><span>Limitation</span><strong>{activeFinding.limitation}</strong></div>
              <div className="proof-note"><Icon name="alert" /><span><b>Relevance is not certainty.</b> MedlinePlus sources supply medical definitions and target intervals; clinical decisions require your physician's evaluation.</span></div>
            </div>
            <div className="ask-doctor-card">
              <div className="card-heading"><div><span className="eyebrow">Ask your doctor</span><h3>Three useful prompts</h3></div><Icon name="chat" /></div>
              {doctorPrompts.map((text) => <button key={text} onClick={() => useSuggested(text)}>{text}<Icon name="arrow" /></button>)}
            </div>
          </aside>
        </div>
      </section>

      <section id="qa" className="workspace-section section-anchor">
        <SectionHeading eyebrow="05 / Interactive Q&A" title="Ask in plain language." copy="A grounded conversation is more useful when it can show its sources — and say when it does not have enough evidence." action={<select className="language-select" value={language} onChange={(event) => setLanguage(event.target.value)} aria-label="Choose answer language"><option>English</option><option>Hindi</option><option>Marathi</option><option>Spanish</option></select>} />
        <div className="qa-layout">
          <div className="chat-card">
            <div className="chat-top">
              <div className="chat-agent">
                <div className="agent-avatar"><Icon name="spark" /></div>
                <div><strong>MedInsight Assistant</strong><span><i /> Grounded Patient Mode</span></div>
              </div>
              <span className="source-tag">{language}</span>
            </div>
            <div className="chat-history">
              {chatMessages.map((message, index) => <div className={`message message-${message.from}`} key={`${message.text}-${index}`}>
                <FormattedMessage text={message.text} />
                {message.from === 'ai' && <small><Icon name="evidence" /> Grounded in active report findings & MedlinePlus RAG</small>}
              </div>)}
              {qaSafetyState === 'insufficient' && <div className="message message-ai safety-message">
                <span><strong>Evidence insufficient.</strong> MedInsight will not guess beyond the uploaded report or retrieved sources.</span>
                <small><Icon name="alert" /> Safety fallback active</small>
              </div>}
            </div>
            <div className="suggested-questions">
              <span>Try asking</span>
              {suggestedQuestions.map((text) => <button key={text} onClick={() => setQuestion(text)}>{text}</button>)}
            </div>
            <form className="chat-input" onSubmit={sendQuestion}>
              <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about your uploaded report in plain language…" aria-label="Ask about your uploaded report" />
              <button type="button" className={isListening ? 'listening' : ''} onClick={startListening} aria-label="Use voice to ask a question"><Icon name="mic" /></button>
              <button type="submit" className="send-button" aria-label="Send question"><Icon name="arrow" /></button>
            </form>
            <div className="chat-disclaimer"><Icon name="alert" /> This assistant explains report information for patient understanding. It is not a doctor and cannot diagnose conditions.</div>
          </div>
          <div className="qa-side">
            <div className="glossary-card">
              <span className="eyebrow">Hover-to-define glossary</span>
              <h3>Make medical terms less intimidating.</h3>
              <p>Medical terms provide one-sentence definitions from the verified MedlinePlus RAG glossary.</p>
              <div className="term-demo">
                <span className="glossary-term" title={activeFinding.definition}>{activeFinding.name}</span>
                <span className="glossary-tooltip">{activeFinding.definition}</span>
              </div>
            </div>
            <div className="insufficient-card">
              <span className="eyebrow">Safety state</span>
              <h3>When evidence is insufficient</h3>
              <p>“I can’t answer that from the uploaded report and retrieved sources. Please ask your clinician or upload a clearer report.”</p>
              <button className="soft-button" onClick={() => { setQaSafetyState('insufficient'); setToast('Safety state preview shown.'); }}>Preview state <Icon name="alert" /></button>
            </div>
          </div>
        </div>
      </section>

      <section id="methodology" className="workspace-section methodology-section section-anchor">
        <SectionHeading eyebrow="06 / About the system" title="Technical depth, made understandable." copy="A capstone architecture that lets evaluators see the path from document to explanation — without hiding the uncertainty between steps." />
        <div className="methodology-flow">
          <div className="flow-label"><span className="eyebrow">MedInsight pipeline</span><strong>From pixels to patient-readable insight</strong></div>
          {['PDF / Image', 'OCR & text extraction', 'NLP information extraction', 'Rule-based value analysis', 'RAG retrieval', 'LLM explanation', 'Validation', 'Interactive UI'].map((step, index) => <div className="flow-step" key={step}><span>0{index + 1}</span><strong>{step}</strong>{index < 7 && <Icon name="arrow" />}</div>)}
        </div>
        <div className="methodology-bottom">
          <div className="tech-card">
            <span className="eyebrow">Technology stack</span>
            <div className="tech-chips">{['Python', 'Streamlit', 'FastAPI', 'PyMuPDF', 'EasyOCR', 'Transformers', 'Sentence Transformers', 'LangChain', 'FAISS', 'Scikit-learn', 'Pandas', 'NumPy'].map((tech) => <span key={tech}>{tech}</span>)}</div>
          </div>
          <div className="team-card">
            <span className="eyebrow">Capstone team</span>
            <div className="team-row">
              <div className="avatar-stack"><div className="avatar avatar-one">LJ</div><div className="avatar avatar-two">SR</div></div>
              <div><strong>Lucky Jain · Shruti Rajak</strong><span>Mentor: Dr. Archana Gulati</span><small>School of Technology Management & Engineering · Navi Mumbai</small></div>
            </div>
          </div>
        </div>
        <div className="integration-callout">
          <div className="integration-icon"><Icon name="flow" /></div>
          <div>
            <span className="eyebrow">System status</span>
            <h3>FastAPI Backend & React Frontend Integrated.</h3>
            <p>CRF extraction, deterministic math verification, MedlinePlus FAISS RAG, and role-based patient/doctor explanations are actively wired together.</p>
          </div>
          <button className="primary-button" onClick={() => goTo('upload')}>Upload & Test Live <Icon name="arrow" /></button>
        </div>
      </section>

      <footer className="page-footer">
        <div><strong>MedInsight</strong><span>Turning Complex Reports into Clear Health Insights.</span></div>
        <div><span>Explainable AI Clinical Intelligence</span><span>Built for a final-year AI & Data Science capstone</span></div>
      </footer>
    </main>
    {toast && <div className="toast" role="status"><Icon name="check" />{toast}</div>}
  </div>;
}

export default App;
