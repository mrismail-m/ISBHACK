import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../../api/client';
import type { TrustReport } from '../../api/types';
import fallbackReport from '../../../../fixtures/api/trust_report.json';

export function TrustReportPage() {
  const [report, setReport] = useState<TrustReport | null>(null);


  useEffect(() => {
    apiClient<TrustReport>('/evaluation/trust-report', { fixtureName: 'trust_report' })
      .then(setReport)
      .catch((err) => {
        // Fallback to the local fixture since the endpoint isn't built yet
        console.warn('API /evaluation/trust-report failed, falling back to mock.', err);
        setReport(fallbackReport as TrustReport);
      });
  }, []);

  if (!report) {
    return <div className="p-8 max-w-4xl mx-auto text-center text-slate-500">Loading Trust Report...</div>;
  }

  const passProbes = report.bias_probes.filter(p => p.passed).length;
  const totalProbes = report.bias_probes.length;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <Link to="/teacher" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Assessments</Link>
        <h2 className="text-3xl font-bold text-slate-800">AI Trust Report</h2>
        <p className="text-slate-500 mt-1">Generated at {new Date(report.generated_at).toLocaleString()} • Model: {report.model_id} • Prompt: {report.prompt_version}</p>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="text-sm font-semibold text-slate-500 mb-1">AI vs Human MAE</h3>
          <p className="text-3xl font-bold text-slate-900">{report.accuracy.ai_vs_human_mae.toFixed(2)}</p>
          <p className="text-xs text-slate-500 mt-1">Human vs Human: {report.accuracy.human_vs_human_mae.toFixed(2)}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="text-sm font-semibold text-slate-500 mb-1">AI vs Human QWK</h3>
          <p className="text-3xl font-bold text-slate-900">{report.accuracy.ai_vs_human_qwk.toFixed(2)}</p>
          <p className="text-xs text-slate-500 mt-1">Human vs Human: {report.accuracy.human_vs_human_qwk.toFixed(2)}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="text-sm font-semibold text-slate-500 mb-1">Consistency (Mean Range)</h3>
          <p className="text-3xl font-bold text-slate-900">{report.consistency.mean_range_marks.toFixed(2)}</p>
          <p className="text-xs text-slate-500 mt-1">Over {report.consistency.runs} runs</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="text-sm font-semibold text-slate-500 mb-1">Bias Probes Passed</h3>
          <p className="text-3xl font-bold text-slate-900">{passProbes}/{totalProbes}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Bias Probes Details</h3>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-slate-600">
                <th className="pb-2 font-medium">Probe</th>
                <th className="pb-2 font-medium text-right">Mean Δ</th>
                <th className="pb-2 font-medium text-right">Max Δ</th>
                <th className="pb-2 font-medium text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {report.bias_probes.map(p => (
                <tr key={p.name}>
                  <td className="py-2 text-slate-800 font-medium">{p.name.replace('_', ' ')}</td>
                  <td className="py-2 text-slate-600 text-right">{p.mean_abs_delta_marks.toFixed(2)}</td>
                  <td className="py-2 text-slate-600 text-right">{p.max_abs_delta_marks.toFixed(2)}</td>
                  <td className="py-2 text-center">
                    {p.passed ? <span className="text-green-600 font-bold">✓ Pass</span> : <span className="text-red-600 font-bold">✗ Fail</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Editor Signals Effectiveness</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-slate-900">{report.editor_signals.pasted_flagged}</p>
                <p className="text-xs text-slate-500 uppercase mt-1">Pasted Flagged</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{report.editor_signals.typed_flagged}</p>
                <p className="text-xs text-slate-500 uppercase mt-1">Typed Flagged</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{report.editor_signals.retyped_flagged}</p>
                <p className="text-xs text-slate-500 uppercase mt-1">Retyped Flagged</p>
              </div>
            </div>
          </div>
          
          <div className="bg-amber-50 p-6 rounded-lg border border-amber-200">
            <h3 className="text-lg font-semibold text-amber-900 mb-2">Limitations</h3>
            <ul className="list-disc pl-5 space-y-1 text-sm text-amber-800">
              {report.limitations.map((limit, idx) => (
                <li key={idx}>{limit}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
