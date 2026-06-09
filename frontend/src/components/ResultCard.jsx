import React, { useState } from 'react';

/* ── Parse LLM feedback into named sections ── */
function parseFeedbackSections(text) {
  if (!text) return {};
  const sections = {};
  // Match **Section Name:** blocks
  const sectionRegex = /\*\*([^*]+?):\*\*/g;
  const matches = [...text.matchAll(sectionRegex)];

  for (let i = 0; i < matches.length; i++) {
    const key = matches[i][1].trim();
    const start = matches[i].index + matches[i][0].length;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    sections[key] = text.slice(start, end).trim();
  }
  return sections;
}

/* ── Inline bold renderer ── */
function renderInline(text) {
  if (!text) return null;
  const parts = [];
  let remaining = text;
  let idx = 0;
  while (remaining.includes('**')) {
    const s = remaining.indexOf('**');
    if (s > 0) parts.push(<span key={idx++}>{remaining.slice(0, s)}</span>);
    remaining = remaining.slice(s + 2);
    const e = remaining.indexOf('**');
    if (e === -1) { parts.push(<span key={idx++}>**{remaining}</span>); remaining = ''; break; }
    parts.push(<strong key={idx++}>{remaining.slice(0, e)}</strong>);
    remaining = remaining.slice(e + 2);
  }
  if (remaining) parts.push(<span key={idx++}>{remaining}</span>);
  return parts;
}

/* ── Section body renderer ── */
function renderSectionBody(body) {
  if (!body) return null;
  const lines = body.split('\n');
  return lines.map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <div key={i} style={{ height: '6px' }} />;
    const isBullet = /^[•\-🔴🟡🟢⚪✅]/.test(trimmed);
    return (
      <div key={i} className={isBullet ? 'fb-bullet' : 'fb-line'}>
        {renderInline(trimmed)}
      </div>
    );
  });
}

/* ── Reusable collapsible note ── */
function CollapsibleNote({ icon, title, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={`fb-benefits ${open ? 'fb-benefits--open' : ''}`} style={{marginTop: '12px'}}>
      <button className="fb-benefits__toggle" onClick={() => setOpen(o => !o)} style={{padding: '12px 18px', fontSize: '0.85rem'}}>
        <span className="fb-benefits__icon" style={{fontSize: '1rem'}}>{icon}</span>
        <span style={{flex: 1, textAlign: 'left', color: 'var(--text-muted)', fontWeight: 500}}>{title}</span>
        <span className={`fb-benefits__chevron ${open ? 'fb-benefits__chevron--open' : ''}`}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </span>
      </button>
      <div className="fb-benefits__body">
        <div style={{padding: '0 18px 14px', fontSize: '0.82rem', lineHeight: 1.7, color: 'var(--text-muted)'}}>
          {children}
        </div>
      </div>
    </div>
  );
}

/* ── Section config ── */
const SECTION_CONFIG = {
  "What You're Doing Well": { icon: '✨', cls: 'fb-sec--praise' },
  "Suggestions for Improvement": { icon: '🎯', cls: 'fb-sec--suggest' },
  "Safety": { icon: '🛡️', cls: 'fb-sec--safety' },
  "Key Focus": { icon: '🔑', cls: 'fb-sec--focus' },
};

/* ── Fallback health benefits for common poses ── */
const POSE_BENEFITS = {
  "Eagle Pose": "• Strengthens calves, ankles, and thighs while improving balance and stability\n• Opens the shoulders and upper back, relieving tension from prolonged sitting\n• Enhances mental focus and concentration through single-point balance\n• Improves joint flexibility in hips, knees, and shoulders",
  "Warrior I": "• Strengthens the legs, core, and back muscles for improved posture\n• Opens the chest and lungs, enhancing respiratory capacity\n• Builds stamina, focus, and determination\n• Stretches the hip flexors and psoas, counteracting prolonged sitting",
  "Warrior II": "• Builds endurance and strength in the legs and ankles\n• Opens the hips, chest, and shoulders simultaneously\n• Improves concentration and body awareness\n• Stimulates abdominal organs and aids digestion",
  "Warrior III": "• Strengthens the legs, ankles, shoulders, and back muscles\n• Improves balance, posture, and full-body coordination\n• Tones the abdominal muscles and improves core stability\n• Enhances memory and concentration through focused balancing",
  "Tree Pose": "• Improves balance and stability while strengthening the standing leg\n• Opens the hips and stretches the inner thighs and groin\n• Promotes mental clarity, focus, and a calm mind\n• Strengthens the ligaments and tendons of the feet and ankles",
  "Mountain Pose": "• Improves posture and body alignment awareness\n• Strengthens the thighs, knees, and ankles\n• Reduces flat feet and promotes healthy foot arches\n• Promotes a sense of calm steadiness and grounding",
  "Downward Dog": "• Strengthens the arms, shoulders, and legs while lengthening the spine\n• Increases blood flow to the brain, improving focus and reducing fatigue\n• Stretches the hamstrings, calves, and Achilles tendons\n• Relieves stress, mild depression, and symptoms of menopause",
  "Cobra Pose": "• Strengthens the spine and firms the buttocks\n• Opens the chest and lungs, improving breathing capacity\n• Stimulates abdominal organs and aids digestion\n• Helps relieve stress and fatigue while soothing sciatica",
  "Triangle Pose": "• Stretches the legs, hips, spine, chest, and shoulders\n• Strengthens the thighs, knees, and ankles\n• Stimulates the abdominal organs and improves digestion\n• Helps relieve stress, anxiety, and lower back pain",
  "Chair Pose": "• Strengthens the ankles, thighs, calves, and spine\n• Stimulates the diaphragm and heart\n• Reduces flat feet and builds lower body resilience\n• Improves balance and builds functional leg strength",
  "Plank Pose": "• Strengthens the arms, wrists, and spine\n• Tones the abdomen and builds core stability\n• Improves posture and overall body alignment\n• Builds endurance and mental resilience",
  "Bridge Pose": "• Stretches the chest, neck, and spine\n• Calms the brain and helps alleviate stress and mild depression\n• Stimulates the lungs, thyroid, and abdominal organs\n• Rejuvenates tired legs and improves digestion",
  "Child's Pose": "• Gently stretches the hips, thighs, and ankles\n• Calms the nervous system and relieves stress and fatigue\n• Relieves back and neck pain when done with head supported\n• Promotes a sense of safety and introspection",
  "Seated Forward Bend": "• Stretches the spine, shoulders, and hamstrings deeply\n• Stimulates the liver, kidneys, and digestive organs\n• Calms the mind and helps relieve stress and anxiety\n• May help relieve symptoms of menopause and reduce fatigue",
  "Crow Pose": "• Strengthens the arms, wrists, and abdominal muscles\n• Stretches the upper back and opens the groins\n• Improves balance, coordination, and body control\n• Builds mental confidence and focus through arm balancing",
  "Boat Pose": "• Strengthens the abdomen, hip flexors, and spine\n• Stimulates the kidneys, thyroid, and intestines\n• Improves digestion and relieves stress\n• Builds core endurance and improves balance",
  "Camel Pose": "• Opens the entire front body — chest, abdomen, and hip flexors\n• Strengthens the back muscles and improves spinal flexibility\n• Stimulates the thyroid and improves respiratory function\n• Helps reduce anxiety and fatigue through heart-opening",
  "Pigeon Pose": "• Deeply stretches the hip flexors and glutes\n• Opens the chest and shoulders when done fully\n• Stimulates the abdominal organs and aids digestion\n• Helps release stored emotional tension in the hips",
  "Lotus Pose": "• Opens the hips and stretches the ankles and knees\n• Calms the brain and promotes deep meditative awareness\n• Stimulates the pelvis, spine, and abdominal organs\n• Helps preserve joint flexibility and ease menstrual discomfort",
  "Half Moon Pose": "• Strengthens the abdomen, ankles, thighs, and spine\n• Improves coordination, balance, and sense of equilibrium\n• Stretches the groins, hamstrings, and calves\n• Relieves stress and improves digestion",
  "Corpse Pose": "• Calms the central nervous system and reduces blood pressure\n• Reduces headache, fatigue, and insomnia\n• Promotes deep muscular relaxation and mental stillness\n• Helps the body integrate the benefits of the preceding practice",
};

/* ── Fuzzy-match pose name to benefits map ── */
function getBenefitsForPose(poseName) {
  if (!poseName) return null;
  const normalized = poseName.toLowerCase().trim();
  for (const [key, val] of Object.entries(POSE_BENEFITS)) {
    if (normalized.includes(key.toLowerCase()) || key.toLowerCase().includes(normalized)) {
      return val;
    }
  }
  return null;
}

/* ── Health Benefits Accordion ── */
function HealthBenefits({ body, poseName }) {
  const [open, setOpen] = useState(false);
  const content = body || getBenefitsForPose(poseName);
  if (!content) return null;
  return (
    <div className={`fb-benefits ${open ? 'fb-benefits--open' : ''}`}>
      <button className="fb-benefits__toggle" onClick={() => setOpen(o => !o)}>
        <span className="fb-benefits__icon">🌿</span>
        <span className="fb-benefits__title">Health Benefits of this Asana</span>
        <span className={`fb-benefits__chevron ${open ? 'fb-benefits__chevron--open' : ''}`}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </span>
      </button>
      <div className="fb-benefits__body">
        <div className="fb-benefits__content">
          {renderSectionBody(content)}
        </div>
      </div>
    </div>
  );
}

/* ── Structured Feedback Renderer ── */
function StructuredFeedback({ feedback, poseName }) {
  if (!feedback) return null;
  const sections = parseFeedbackSections(feedback);

  // Extract header lines (pose name + score) before first section
  const firstBold = feedback.indexOf('**');
  const sectionKeys = Object.keys(sections);
  let headerText = '';
  if (firstBold >= 0 && sectionKeys.length > 0) {
    const firstSectionStart = feedback.indexOf(`**${sectionKeys[0]}:**`);
    if (firstSectionStart > 0) {
      headerText = feedback.slice(0, firstSectionStart).trim();
    }
  }

  // Parse score from header
  const scoreMatch = headerText.match(/Score:\s*(\d+)\/100\s*[—–-]\s*(.+)/);

  return (
    <div className="fb-container">
      {/* Section Title */}
      <div className="fb-header">
        <div className="fb-header__icon">🧘</div>
        <h3 className="fb-header__title">Instructor Feedback</h3>
        {scoreMatch && (
          <div className="fb-header__score">
            {scoreMatch[1]}<span>/100</span>
          </div>
        )}
      </div>

      {/* Main Sections */}
      <div className="fb-sections">
        {Object.entries(SECTION_CONFIG).map(([key, { icon, cls }]) => {
          const body = sections[key];
          if (!body) return null;
          return (
            <div key={key} className={`fb-sec ${cls}`}>
              <div className="fb-sec__header">
                <span className="fb-sec__icon">{icon}</span>
                <h4 className="fb-sec__title">{key}</h4>
              </div>
              <div className="fb-sec__body">
                {renderSectionBody(body)}
              </div>
            </div>
          );
        })}
      </div>

      {/* Health Benefits Accordion */}
      <HealthBenefits body={sections["Health Benefits"]} poseName={poseName} />

      {/* Disclaimer — collapsible */}
      <div style={{padding: '0 16px 12px'}}>
        <CollapsibleNote icon="⚕️" title="Medical Disclaimer" defaultOpen={false}>
          This AI-generated feedback is for informational purposes only and is not a substitute for professional guidance.
          Individuals with any specific health conditions, injuries, or medical concerns are strongly advised to consult with a qualified <strong>Medical Practitioner</strong> and
          an experienced <strong>Yoga Practitioner</strong> before attempting or continuing any asana practice.
        </CollapsibleNote>
      </div>
    </div>
  );
}


export default function ResultCard({ evaluation, feedback, comparison }) {
  if (!evaluation) return null;

  const getScoreClass = (label) => {
    switch (label) {
      case 'correct': return 'score-correct';
      case 'needs_adjustment': return 'score-adjust';
      case 'incorrect': return 'score-incorrect';
      default: return 'score-unknown';
    }
  };

  const scoreText = evaluation.correctness_label === 'correct' ? 'Great Form' :
                    evaluation.correctness_label === 'needs_adjustment' ? 'Needs Adjustment' :
                    evaluation.correctness_label === 'incorrect' ? 'Needs Correction' : 
                    'Basic Assessment';

  const icon = evaluation.correctness_label === 'correct' ? '✅' :
               evaluation.correctness_label === 'needs_adjustment' ? '🟡' :
               evaluation.correctness_label === 'incorrect' ? '🔴' : 'ℹ️';

  // Confidence display: contextualize for 82-class classifier
  const rawConf = evaluation.pose_confidence ?? 0;
  const confPercent = (rawConf * 100).toFixed(0);
  const confLabel = confPercent >= 50 ? 'High' : confPercent >= 20 ? 'Moderate' : 'Low';

  return (
    <div className="card" style={{marginTop: '20px'}}>
      
      {/* Header section */}
      <div className="results-header">
        <div>
          <div className="pose-name">{evaluation.pose_name}</div>
          {evaluation.sanskrit_name && (
            <div className="sanskrit">{evaluation.sanskrit_name}</div>
          )}
        </div>
        
        <div style={{marginLeft: 'auto', display: 'flex', gap: '16px', alignItems: 'center'}}>
          <div className={`score-badge ${getScoreClass(evaluation.correctness_label)}`}>
            {icon} {(evaluation.overall_score ?? 0).toFixed(0)} <span style={{fontSize: '0.8em', opacity: 0.7}}>/100</span>
          </div>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="results-grid">
        <div className="stat-card" style={{background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)'}}>
          <div className="stat-label">AI Assessment</div>
          <div className="stat-value">{scoreText}</div>
          <div className="stat-sub">
            {confLabel} pose match ({confPercent}%)
          </div>
        </div>
        
        {comparison && comparison.historical_context_available && (
          <div className="stat-card progress-card" style={{background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)'}}>
            <div className="stat-label">Progress</div>
            <div className="stat-value">
              {comparison.current_vs_previous_delta > 0 && <span className="delta-positive">+{comparison.current_vs_previous_delta.toFixed(0)}</span>}
              {comparison.current_vs_previous_delta < 0 && <span className="delta-negative">{comparison.current_vs_previous_delta.toFixed(0)}</span>}
              {comparison.current_vs_previous_delta === 0 && <span className="delta-neutral">No Change</span>}
            </div>
            
            <div className="areas-list" style={{marginTop: '8px'}}>
              {comparison.improved_areas?.map(area => <span key={area} className="area-tag improved">{area} ↑</span>)}
              {comparison.declined_areas?.map(area => <span key={area} className="area-tag declined">{area} ↓</span>)}
            </div>
          </div>
        )}
      </div>

      {/* Safety Flags */}
      {evaluation.safety_flags?.length > 0 && (
        <div className="safety-flags" style={{marginBottom: '24px'}}>
          {evaluation.safety_flags.map((flag, idx) => (
            <div key={idx} className="safety-flag">
              <strong>Safety Note:</strong> {flag}
            </div>
          ))}
        </div>
      )}

      {/* ── Structured Instructor Feedback ── */}
      <StructuredFeedback feedback={feedback} poseName={evaluation.pose_name} />

      {/* Specific Issues */}
      {evaluation.issues?.length > 0 && (
        <>
          <h4 className="section-header">Specific Issues Detected</h4>
          <div className="issues-list">
            {evaluation.issues.map((issue, idx) => {
              const severityClass = issue.severity;
              const severityIcon = issue.severity === 'major' ? '🔴' : issue.severity === 'moderate' ? '🟡' : '🟢';
              
              return (
                <div key={idx} className={`issue-item ${severityClass}`}>
                  <div className="issue-icon">{severityIcon}</div>
                  <div className="issue-body">
                    <div className="issue-instruction">{issue.instruction_key}</div>
                    <div className="issue-detail">
                      {issue.description}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
      
      {evaluation.issues?.length === 0 && evaluation.correctness_label === 'correct' && (
        <div style={{padding: '24px', textAlign: 'center', background: 'rgba(34,197,94,0.05)', borderRadius: 'var(--radius-md)', color: 'var(--success-400)'}}>
          <div style={{fontSize: '2rem', marginBottom: '8px'}}>🌟</div>
          <strong>Excellent Form!</strong> No specific alignment issues were detected.
        </div>
      )}

      {/* Reliability info — collapsible */}
      {evaluation.reliability_reason && evaluation.evaluation_status !== 'low_confidence' && (
        <CollapsibleNote icon="ℹ️" title="Detection Note" defaultOpen={false}>
          {evaluation.reliability_reason}
        </CollapsibleNote>
      )}

    </div>
  );
}
