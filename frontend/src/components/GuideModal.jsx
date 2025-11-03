import React from 'react';
import './GuideModal.css';

export default function GuideModal({ isOpen, onClose, guideType }) {
  if (!isOpen) return null;

  const guides = {
    general: {
      title: '📖 User Guide',
      sections: [
        {
          heading: 'Getting Started',
          content: [
            'TEMPORA is an intelligent calendar system that helps you optimize your schedule for health and productivity.',
            'The main calendar shows your events with color-coded categories: Work (blue), Meetings (purple), Personal (green), Recreational (orange), and Meals (yellow).',
            'Click on any event to view details, edit, or delete. Use the navigation arrows to browse weeks.',
          ]
        },
        {
          heading: 'Adding Events',
          content: [
            'Click the "Add Event" button or click on a time slot in the calendar.',
            'Fill in the title, start/end times, and select the appropriate category.',
            'Choose the right category: Work for focus tasks, Meeting for collaborative sessions, Personal for obligations, Recreational for active recovery.',
            'Events are validated automatically to prevent conflicts and sleep intrusions.',
          ]
        },
        {
          heading: 'Scores & Analytics',
          content: [
            '**Health Score (0-100)**: Measures scheduling sustainability - work/life balance (25%), sleep respect (20%), focus blocks (20%), meeting load (15%), recovery time (20%).',
            '**Productivity Score (0-100)**: Measures time allocation efficiency - block structure (30%), fragmentation (15%), schedule balance (20%), meeting efficiency (20%), recovery support (15%).',
            '**Statistics**: View weekly trends, score history, and improvement opportunities.',
            'Both scores based on 20+ peer-reviewed research studies.',
          ]
        },
        {
          heading: 'Understanding Recommendations',
          content: [
            '**Top Priority Recommendations**: Detailed action cards with step-by-step guidance for the most impactful improvements.',
            '**Additional Insights**: Other detected issues and optimization opportunities not in top 3 priorities.',
            'Each recommendation includes: what\'s wrong, why it matters (research-backed), what to do, and how to implement.',
            'Focus on top priorities first - they provide the biggest impact on your scores.',
          ]
        },
        {
          heading: 'Event Categories',
          content: [
            '**Work (Blue)**: Focus work tasks and projects. Counted in work hours and focus blocks.',
            '**Meeting (Purple)**: Collaborative meetings. Tracked for meeting load and back-to-back patterns.',
            '**Personal (Green)**: Personal obligations. Contributes to work-life balance.',
            '**Recreational (Orange)**: Active recovery activities (exercise, hobbies, social). 4x weight in recovery scoring - most important for health!',
            '**Meal (Yellow)**: Meal breaks. Also counts as active recovery with 4x weight.',
            'Note: Breaks are calculated from gaps - don\'t create break events!',
          ]
        },
        {
          heading: 'Navigation',
          content: [
            'Use arrow buttons to navigate between weeks.',
            'Current week is highlighted in the date display.',
            'All changes sync automatically with the backend.',
          ]
        }
      ]
    },
    health: {
      title: '🏥 Health Score Guide',
      sections: [
        {
          heading: 'What is Health Score?',
          content: [
            'Health Score (0-100) measures how well your schedule supports physical and mental wellbeing.',
            'Based on 16+ peer-reviewed studies from WHO, Microsoft, UCI, AASM, and NASA.',
            'Higher scores indicate better work/life balance and sustainable scheduling practices.',
          ]
        },
        {
          heading: 'Metrics Explained',
          content: [
            '**Work/Life Balance (25%)**: Total work hours per week, long days (>10h), weekend/night work. Highest priority for sustainable scheduling.',
            '**Sleep Respect (20%)**: Events scheduled during sleep hours (default: 11PM-7AM). Critical base requirement for health.',
            '**Focus Blocks (20%)**: Uninterrupted work blocks of 90+ minutes for deep work. Essential for cognitive performance.',
            '**Meeting Load (15%)**: Meeting hours as % of work time, back-to-back meetings. Research shows gaps reduce stress by 13%.',
            '**Recovery Time (20%)**: Active recovery (Recreational/Meal events). Increased weight for burnout prevention - 16x more effective than passive gaps.',
          ]
        },
        {
          heading: 'Top Priority Recommendations',
          content: [
            '**Manual Action Cards**: Detailed step-by-step guidance for the most critical health improvements.',
            'Each card includes: Problem statement, why it matters (research-backed), what to do, and action steps.',
            '**Additional Insights**: Other detected issues and suggestions not in top priorities.',
            'Focus on the top 3 recommendations first - they have the biggest impact on your health score.',
          ]
        },
        {
          heading: 'Improving Your Score',
          content: [
            '**Target: 80+** for excellent health-oriented scheduling.',
            '**Prioritize Active Recovery**: Schedule Recreational and Meal events - now 20% of score (was 15%).',
            'Leave small gaps (5-10min) between meetings for mental reset - proven to restore brain activity.',
            'Limit work hours to <48h/week and avoid long days (>10h) for sustainable performance.',
            '**Protect Sleep Hours**: Move or reschedule conflicting events - sleep is 20% of score but critical base requirement.',
            'Create 90+ minute focus blocks for uninterrupted deep work.',
          ]
        },
        {
          heading: 'Research Foundation',
          content: [
            'WHO: 55+ hour weeks increase stroke risk by 35% and coronary heart disease by 17%.',
            'Microsoft Research: 10-min gaps between meetings restore brain activity and reduce stress by 13%.',
            'Stanford Study: Active recovery (Recreational/Meal) is 16x more effective than passive rest for burnout prevention.',
            'AASM Guidelines: 7-9 hours sleep critical for circadian health and cognitive function.',
            'UCI Study: 23 minutes needed to refocus after context switching interruptions.',
          ]
        }
      ]
    },
    productivity: {
      title: '⚡ Productivity Score Guide',
      sections: [
        {
          heading: 'What is Productivity Score?',
          content: [
            'Productivity Score (0-100) measures how efficiently your schedule supports deep work and sustained output.',
            'Based on 7+ studies on time blocking, context switching costs, and planning research.',
            'Higher scores indicate better time allocation efficiency and work structure. This is about "smart allocation" not "more work".',
          ]
        },
        {
          heading: 'Metrics Explained',
          content: [
            '**Block Structure (30%)**: Deep work blocks of 90+ minutes. Optimal: 10-15h/week. Time blocking improves productivity 3x.',
            '**Fragmentation (15%)**: Context switches between categories. Each switch costs 15 min recovery. Reduced weight for realistic schedules.',
            '**Schedule Balance (20%)**: Combined utilization + buffer. Optimal: 75-85% scheduled, 15-25% buffer for flexibility.',
            '**Meeting Efficiency (20%)**: Meeting-to-work flow. Meetings followed by implementation work within 2h maximize value. Increased weight.',
            '**Recovery Support (15%)**: Non-work recovery time. Rest prevents burnout and sustains long-term productivity. Increased weight.',
          ]
        },
        {
          heading: 'Efficiency Metrics',
          content: [
            '**Deep Work Hours**: Total time in focused 90+ minute uninterrupted blocks. Target: 10-15h/week.',
            '**Context Switches**: Number of category transitions per week. Each costs ~15 minutes. Target: ≤15 weighted transitions.',
            '**Wasted Hours**: Time lost to fragmentation from context switching (transitions × 15 min).',
            '**Work Utilization**: Percentage of available work hours scheduled. Sweet spot: 75-85%.',
            '**Buffer Hours**: Unscheduled slack time for overruns and unexpected tasks.',
          ]
        },
        {
          heading: 'Top Priority Recommendations',
          content: [
            '**Manual Action Cards**: Detailed step-by-step guidance for the most impactful productivity improvements.',
            'Each card includes: Problem identified, impact explanation (research-backed), recommended action, and implementation steps.',
            '**Additional Insights**: Other inefficiencies and optimization opportunities not in top priorities.',
            'Start with top 3 recommendations - they provide the biggest productivity gains.',
          ]
        },
        {
          heading: 'Improving Your Score',
          content: [
            '**Target: 75+** for highly productive scheduling patterns.',
            '**Create Deep Work Blocks**: Schedule 90+ minute uninterrupted work sessions. Now 30% of score - most important factor.',
            '**Batch Similar Tasks**: Group similar work together to reduce context switches (15% of score).',
            '**Meeting Flow**: Schedule work immediately after related meetings to leverage fresh context (20% of score - increased).',
            '**Maintain Balance**: Keep 75-85% scheduled with 15-25% buffer for flexibility (20% of score).',
            '**Prioritize Recovery**: Schedule 10h+ of non-work time per week. Rest sustains productivity (15% of score - increased).',
          ]
        },
        {
          heading: 'Research Foundation',
          content: [
            'Mark et al. (2008): 15 minutes average to refocus after context switch (range: 9.5-23 min).',
            'Cal Newport (Deep Work): 90+ minute blocks required for flow state and maximum cognitive output.',
            'ETTO Principle: Buffer time (5-10%) enables efficiency-thoroughness balance and adaptability.',
            'Rogelberg et al.: Meeting-adjacent work blocks maximize context retention and implementation effectiveness.',
            'Lancet (2018) & WHO: 7-14h/week recovery time optimal for sustained performance and burnout prevention.',
          ]
        }
      ]
    }
  };

  const guide = guides[guideType] || guides.general;

  return (
    <div className="guide-modal-overlay" onClick={onClose}>
      <div className="guide-modal-content" onClick={e => e.stopPropagation()}>
        <div className="guide-modal-header">
          <h2>{guide.title}</h2>
          <button className="guide-close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="guide-modal-body">
          {guide.sections.map((section, idx) => (
            <div key={idx} className="guide-section">
              <h3>{section.heading}</h3>
              {section.content.map((paragraph, pIdx) => (
                <p key={pIdx} dangerouslySetInnerHTML={{ 
                  __html: paragraph.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') 
                }} />
              ))}
            </div>
          ))}
        </div>
        
        <div className="guide-modal-footer">
          <button className="guide-btn" onClick={onClose}>Got it!</button>
        </div>
      </div>
    </div>
  );
}
