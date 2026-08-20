import { useState } from "react";
import { api } from "../../services/api";
import type { InterviewType, CreateInterviewRequest } from "../../types";
import { Modal, ModalHeader, ModalBody, ModalFooter } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Label } from "../ui/Label";
import { toast } from "../ui/Toast";
import { cn } from "../../lib/cn";

interface InterviewSchedulerProps {
  onClose: () => void;
  onCreated: () => void;
}

type Step = "candidate" | "position" | "config" | "review";

export function InterviewScheduler({ onClose, onCreated }: InterviewSchedulerProps) {
  const [step, setStep] = useState<Step>("candidate");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Form data
  const [formData, setFormData] = useState<CreateInterviewRequest>({
    candidate_name: "",
    candidate_email: "",
    candidate_phone: "",
    candidate_linkedin: "",
    position_title: "",
    position_description: "",
    required_skills: [],
    interview_type: "mixed",
    duration_minutes: 45,
    scheduled_time: "",
    meeting_url: "",
  });

  const [skillInput, setSkillInput] = useState("");

  const steps: { key: Step; label: string; icon: string }[] = [
    { key: "candidate", label: "Candidate", icon: "1" },
    { key: "position", label: "Position", icon: "2" },
    { key: "config", label: "Configuration", icon: "3" },
    { key: "review", label: "Review", icon: "4" },
  ];

  const currentStepIndex = steps.findIndex((s) => s.key === step);

  const updateField = <K extends keyof CreateInterviewRequest>(
    field: K,
    value: CreateInterviewRequest[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const addSkill = () => {
    if (skillInput.trim() && !formData.required_skills.includes(skillInput.trim())) {
      updateField("required_skills", [...formData.required_skills, skillInput.trim()]);
      setSkillInput("");
    }
  };

  const removeSkill = (skill: string) => {
    updateField(
      "required_skills",
      formData.required_skills.filter((s) => s !== skill)
    );
  };

  const validateStep = (currentStep: Step): boolean => {
    const newErrors: Record<string, string> = {};

    switch (currentStep) {
      case "candidate":
        if (!formData.candidate_name.trim()) {
          newErrors.candidate_name = "Name is required";
        }
        if (!formData.candidate_email.trim()) {
          newErrors.candidate_email = "Email is required";
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.candidate_email)) {
          newErrors.candidate_email = "Invalid email format";
        }
        break;
      case "position":
        if (!formData.position_title.trim()) {
          newErrors.position_title = "Position title is required";
        }
        break;
      case "config":
        if (!formData.scheduled_time) {
          newErrors.scheduled_time = "Schedule time is required";
        } else {
          const scheduledDate = new Date(formData.scheduled_time);
          if (scheduledDate <= new Date()) {
            newErrors.scheduled_time = "Schedule time must be in the future";
          }
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (!validateStep(step)) return;

    const stepOrder: Step[] = ["candidate", "position", "config", "review"];
    const currentIndex = stepOrder.indexOf(step);
    if (currentIndex < stepOrder.length - 1) {
      setStep(stepOrder[currentIndex + 1]);
    }
  };

  const handleBack = () => {
    const stepOrder: Step[] = ["candidate", "position", "config", "review"];
    const currentIndex = stepOrder.indexOf(step);
    if (currentIndex > 0) {
      setStep(stepOrder[currentIndex - 1]);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await api.createInterview(formData);
      toast.success("Interview scheduled", `Interview with ${formData.candidate_name} has been scheduled`);
      onCreated();
    } catch (err) {
      console.error("Failed to create interview:", err);
      toast.error("Failed to schedule interview", "Please try again");
    } finally {
      setLoading(false);
    }
  };

  const interviewTypes: { value: InterviewType; label: string; icon: string; description: string }[] = [
    {
      value: "technical",
      label: "Technical",
      icon: "💻",
      description: "Coding, system design, technical knowledge",
    },
    {
      value: "behavioral",
      label: "Behavioral",
      icon: "🤝",
      description: "STAR method, soft skills, teamwork",
    },
    {
      value: "hr",
      label: "HR",
      icon: "👤",
      description: "Culture fit, career goals, logistics",
    },
    {
      value: "mixed",
      label: "Mixed",
      icon: "📋",
      description: "Combination of all interview types",
    },
  ];

  return (
    <Modal open={true} onClose={onClose} size="lg">
      <ModalHeader onClose={onClose}>Schedule AI Interview</ModalHeader>

      {/* Step Indicator */}
      <div className="px-6 py-4 border-b dark:border-slate-700">
        <div className="flex items-center justify-between">
          {steps.map((s, i) => (
            <div key={s.key} className="flex items-center">
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
                  i <= currentStepIndex
                    ? "bg-purple-600 text-white"
                    : "bg-slate-200 dark:bg-slate-700 text-slate-500"
                )}
              >
                {s.icon}
              </div>
              <span
                className={cn(
                  "ml-2 text-sm font-medium hidden sm:block",
                  i <= currentStepIndex
                    ? "text-slate-900 dark:text-white"
                    : "text-slate-500"
                )}
              >
                {s.label}
              </span>
              {i < steps.length - 1 && (
                <div
                  className={cn(
                    "w-12 h-0.5 mx-2",
                    i < currentStepIndex
                      ? "bg-purple-600"
                      : "bg-slate-200 dark:bg-slate-700"
                  )}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      <ModalBody className="space-y-6">
        {/* Step 1: Candidate Info */}
        {step === "candidate" && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="candidate_name">Candidate Name *</Label>
              <Input
                id="candidate_name"
                value={formData.candidate_name}
                onChange={(e) => updateField("candidate_name", e.target.value)}
                placeholder="John Doe"
                error={errors.candidate_name}
              />
            </div>
            <div>
              <Label htmlFor="candidate_email">Email *</Label>
              <Input
                id="candidate_email"
                type="email"
                value={formData.candidate_email}
                onChange={(e) => updateField("candidate_email", e.target.value)}
                placeholder="john@example.com"
                error={errors.candidate_email}
              />
            </div>
            <div>
              <Label htmlFor="candidate_phone">Phone (Optional)</Label>
              <Input
                id="candidate_phone"
                value={formData.candidate_phone || ""}
                onChange={(e) => updateField("candidate_phone", e.target.value)}
                placeholder="+1 (555) 123-4567"
              />
            </div>
            <div>
              <Label htmlFor="candidate_linkedin">LinkedIn Profile (Optional)</Label>
              <Input
                id="candidate_linkedin"
                value={formData.candidate_linkedin || ""}
                onChange={(e) => updateField("candidate_linkedin", e.target.value)}
                placeholder="https://linkedin.com/in/johndoe"
              />
            </div>
          </div>
        )}

        {/* Step 2: Position Info */}
        {step === "position" && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="position_title">Position Title *</Label>
              <Input
                id="position_title"
                value={formData.position_title}
                onChange={(e) => updateField("position_title", e.target.value)}
                placeholder="Senior Software Engineer"
                error={errors.position_title}
              />
            </div>
            <div>
              <Label htmlFor="position_description">Position Description (Optional)</Label>
              <textarea
                id="position_description"
                value={formData.position_description || ""}
                onChange={(e) => updateField("position_description", e.target.value)}
                placeholder="Brief description of the role and responsibilities..."
                className="w-full px-3 py-2 border rounded-lg dark:border-slate-700 dark:bg-slate-800 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none resize-none"
                rows={3}
              />
            </div>
            <div>
              <Label>Required Skills</Label>
              <div className="flex gap-2 mb-2">
                <Input
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  placeholder="Add a skill..."
                  onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
                />
                <Button type="button" onClick={addSkill} variant="outline">
                  Add
                </Button>
              </div>
              {formData.required_skills.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.required_skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 text-sm"
                    >
                      {skill}
                      <button
                        type="button"
                        onClick={() => removeSkill(skill)}
                        className="hover:text-purple-600 dark:hover:text-purple-400"
                      >
                        <span className="sr-only">Remove</span>
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Configuration */}
        {step === "config" && (
          <div className="space-y-6">
            <div>
              <Label>Interview Type *</Label>
              <div className="grid grid-cols-2 gap-3 mt-2">
                {interviewTypes.map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => updateField("interview_type", type.value)}
                    className={cn(
                      "p-4 rounded-lg border-2 text-left transition-all",
                      formData.interview_type === type.value
                        ? "border-purple-500 bg-purple-50 dark:bg-purple-900/20"
                        : "border-slate-200 dark:border-slate-700 hover:border-purple-300"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{type.icon}</span>
                      <span className="font-medium text-slate-900 dark:text-white">
                        {type.label}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {type.description}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="duration">Duration (minutes)</Label>
                <select
                  id="duration"
                  value={formData.duration_minutes}
                  onChange={(e) => updateField("duration_minutes", parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg dark:border-slate-700 dark:bg-slate-800 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                >
                  <option value={30}>30 minutes</option>
                  <option value={45}>45 minutes</option>
                  <option value={60}>60 minutes</option>
                  <option value={90}>90 minutes</option>
                </select>
              </div>
              <div>
                <Label htmlFor="scheduled_time">Scheduled Time *</Label>
                <Input
                  id="scheduled_time"
                  type="datetime-local"
                  value={formData.scheduled_time}
                  onChange={(e) => updateField("scheduled_time", e.target.value)}
                  error={errors.scheduled_time}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="meeting_url">Meeting URL (Optional)</Label>
              <Input
                id="meeting_url"
                value={formData.meeting_url || ""}
                onChange={(e) => updateField("meeting_url", e.target.value)}
                placeholder="https://meet.google.com/..."
              />
              <p className="mt-1 text-xs text-slate-500">
                Leave empty to have the system create a meeting link
              </p>
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {step === "review" && (
          <div className="space-y-6">
            <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Interview Summary
              </h3>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Candidate</p>
                  <p className="font-medium text-slate-900 dark:text-white">
                    {formData.candidate_name}
                  </p>
                  <p className="text-slate-600 dark:text-slate-300">
                    {formData.candidate_email}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Position</p>
                  <p className="font-medium text-slate-900 dark:text-white">
                    {formData.position_title}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Interview Type</p>
                  <p className="font-medium text-slate-900 dark:text-white capitalize">
                    {interviewTypes.find((t) => t.value === formData.interview_type)?.icon}{" "}
                    {formData.interview_type}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 dark:text-slate-400">Duration</p>
                  <p className="font-medium text-slate-900 dark:text-white">
                    {formData.duration_minutes} minutes
                  </p>
                </div>
                <div className="col-span-2">
                  <p className="text-slate-500 dark:text-slate-400">Scheduled For</p>
                  <p className="font-medium text-slate-900 dark:text-white">
                    {formData.scheduled_time
                      ? new Date(formData.scheduled_time).toLocaleString()
                      : "Not set"}
                  </p>
                </div>
                {formData.required_skills.length > 0 && (
                  <div className="col-span-2">
                    <p className="text-slate-500 dark:text-slate-400 mb-2">Required Skills</p>
                    <div className="flex flex-wrap gap-2">
                      {formData.required_skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-2 py-1 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 text-xs"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">🤖</span>
                <div>
                  <p className="font-medium text-purple-900 dark:text-purple-100">
                    AI Interview Features
                  </p>
                  <ul className="mt-2 text-sm text-purple-700 dark:text-purple-300 space-y-1">
                    <li>• AI will generate tailored interview questions</li>
                    <li>• Text-to-Speech for AI speaking capability</li>
                    <li>• Automatic transcript analysis and scoring</li>
                    <li>• Comprehensive evaluation report</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </ModalBody>

      <ModalFooter>
        <div className="flex justify-between w-full">
          <Button
            variant="outline"
            onClick={step === "candidate" ? onClose : handleBack}
          >
            {step === "candidate" ? "Cancel" : "Back"}
          </Button>
          {step === "review" ? (
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? "Scheduling..." : "Schedule Interview"}
            </Button>
          ) : (
            <Button onClick={handleNext}>Next</Button>
          )}
        </div>
      </ModalFooter>
    </Modal>
  );
}
