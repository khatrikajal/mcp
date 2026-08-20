import type { InterviewQuestion, InterviewRecommendation } from "../../types";
import { cn } from "../../lib/cn";

interface CandidateScorecardProps {
  overallScore: number;
  recommendation: InterviewRecommendation;
  competencyScores: Record<string, number>;
  questions: InterviewQuestion[];
}

export function CandidateScorecard({
  overallScore,
  recommendation,
  competencyScores,
  questions,
}: CandidateScorecardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-emerald-600 dark:text-emerald-400";
    if (score >= 6) return "text-blue-600 dark:text-blue-400";
    if (score >= 4) return "text-amber-600 dark:text-amber-400";
    return "text-red-600 dark:text-red-400";
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 8) return "bg-emerald-100 dark:bg-emerald-900/30";
    if (score >= 6) return "bg-blue-100 dark:bg-blue-900/30";
    if (score >= 4) return "bg-amber-100 dark:bg-amber-900/30";
    return "bg-red-100 dark:bg-red-900/30";
  };

  const getOverallScoreGrade = (score: number) => {
    if (score >= 90) return { grade: "A+", color: "text-emerald-600", desc: "Exceptional" };
    if (score >= 85) return { grade: "A", color: "text-emerald-600", desc: "Excellent" };
    if (score >= 80) return { grade: "A-", color: "text-emerald-500", desc: "Very Good" };
    if (score >= 75) return { grade: "B+", color: "text-blue-600", desc: "Good" };
    if (score >= 70) return { grade: "B", color: "text-blue-500", desc: "Above Average" };
    if (score >= 65) return { grade: "B-", color: "text-blue-400", desc: "Average" };
    if (score >= 60) return { grade: "C+", color: "text-amber-600", desc: "Below Average" };
    if (score >= 55) return { grade: "C", color: "text-amber-500", desc: "Needs Work" };
    if (score >= 50) return { grade: "C-", color: "text-amber-400", desc: "Weak" };
    return { grade: "F", color: "text-red-600", desc: "Not Recommended" };
  };

  const recommendationDetails: Record<
    InterviewRecommendation,
    { icon: string; description: string; action: string }
  > = {
    strong_hire: {
      icon: "🌟",
      description: "Exceptional candidate who exceeds all requirements",
      action: "Extend offer immediately",
    },
    hire: {
      icon: "✅",
      description: "Strong candidate who meets requirements well",
      action: "Proceed with offer process",
    },
    maybe: {
      icon: "🤔",
      description: "Candidate has potential but some concerns exist",
      action: "Consider additional interview or discussion",
    },
    no_hire: {
      icon: "⚠",
      description: "Candidate does not meet key requirements",
      action: "Do not proceed with this candidate",
    },
    strong_no_hire: {
      icon: "❌",
      description: "Significant concerns about fit or capability",
      action: "Decline and move to other candidates",
    },
  };

  const gradeInfo = getOverallScoreGrade(overallScore);
  const recInfo = recommendationDetails[recommendation];

  // Calculate category statistics
  const categoryStats: Record<string, { avg: number; count: number }> = {};
  questions.forEach((q) => {
    if (q.score !== null && q.score !== undefined) {
      const cat = q.question_type;
      if (!categoryStats[cat]) {
        categoryStats[cat] = { avg: 0, count: 0 };
      }
      categoryStats[cat].avg += q.score;
      categoryStats[cat].count += 1;
    }
  });
  Object.keys(categoryStats).forEach((cat) => {
    categoryStats[cat].avg = Math.round(
      (categoryStats[cat].avg / categoryStats[cat].count) * 10
    ) / 10;
  });

  return (
    <div className="space-y-6">
      {/* Score Overview */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Overall Score Circle */}
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border dark:border-slate-700 text-center">
          <div className="relative w-32 h-32 mx-auto">
            {/* Background circle */}
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="56"
                className="fill-none stroke-slate-200 dark:stroke-slate-700"
                strokeWidth="12"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                className={cn(
                  "fill-none transition-all duration-1000",
                  overallScore >= 70
                    ? "stroke-emerald-500"
                    : overallScore >= 55
                    ? "stroke-amber-500"
                    : "stroke-red-500"
                )}
                strokeWidth="12"
                strokeLinecap="round"
                strokeDasharray={`${(overallScore / 100) * 352} 352`}
              />
            </svg>
            {/* Score text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={cn("text-3xl font-bold", gradeInfo.color)}>
                {gradeInfo.grade}
              </span>
              <span className="text-sm text-slate-500">{overallScore}%</span>
            </div>
          </div>
          <p className="mt-4 text-sm font-medium text-slate-600 dark:text-slate-400">
            {gradeInfo.desc}
          </p>
        </div>

        {/* Recommendation */}
        <div className="md:col-span-2 bg-white dark:bg-slate-800 rounded-xl p-6 border dark:border-slate-700">
          <div className="flex items-start gap-4">
            <span className="text-4xl">{recInfo.icon}</span>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white capitalize">
                {recommendation.replace("_", " ")}
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mt-1">
                {recInfo.description}
              </p>
              <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Recommended Action:
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {recInfo.action}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Category Performance */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Performance by Category
        </h3>
        <div className="grid md:grid-cols-3 gap-4">
          {Object.entries(categoryStats).map(([category, { avg, count }]) => (
            <div
              key={category}
              className={cn(
                "p-4 rounded-lg border",
                getScoreBgColor(avg)
              )}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 capitalize">
                    {category}
                  </p>
                  <p className={cn("text-2xl font-bold", getScoreColor(avg))}>
                    {avg}/10
                  </p>
                </div>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {count} Q{count > 1 ? "s" : ""}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Competency Radar (simplified bar chart) */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Competency Analysis
        </h3>
        <div className="space-y-4">
          {Object.entries(competencyScores)
            .sort(([, a], [, b]) => b - a)
            .map(([competency, score]) => (
              <div key={competency} className="flex items-center gap-4">
                <div className="w-40">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize truncate">
                    {competency.replace("_", " ")}
                  </p>
                </div>
                <div className="flex-1">
                  <div className="h-6 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden relative">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-500",
                        score >= 8
                          ? "bg-gradient-to-r from-emerald-400 to-emerald-500"
                          : score >= 6
                          ? "bg-gradient-to-r from-blue-400 to-blue-500"
                          : score >= 4
                          ? "bg-gradient-to-r from-amber-400 to-amber-500"
                          : "bg-gradient-to-r from-red-400 to-red-500"
                      )}
                      style={{ width: `${score * 10}%` }}
                    />
                    <div className="absolute inset-0 flex items-center justify-end pr-2">
                      <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
                        {score}/10
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Question Score Distribution */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Question Score Distribution
        </h3>
        <div className="flex items-end gap-2 h-32">
          {questions.map((q, i) => {
            const score = q.score ?? 0;
            const height = (score / 10) * 100;
            return (
              <div
                key={q.id}
                className="flex-1 flex flex-col items-center gap-1"
                title={`Q${i + 1}: ${score}/10`}
              >
                <div
                  className={cn(
                    "w-full rounded-t transition-all",
                    score >= 8
                      ? "bg-emerald-500"
                      : score >= 6
                      ? "bg-blue-500"
                      : score >= 4
                      ? "bg-amber-500"
                      : "bg-red-500"
                  )}
                  style={{ height: `${height}%` }}
                />
                <span className="text-xs text-slate-500">Q{i + 1}</span>
              </div>
            );
          })}
        </div>
        <div className="mt-4 flex justify-center gap-6 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-emerald-500" /> 8-10 Excellent
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-blue-500" /> 6-7 Good
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-amber-500" /> 4-5 Fair
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-500" /> 0-3 Poor
          </span>
        </div>
      </div>
    </div>
  );
}
