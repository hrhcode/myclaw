import type { Automation, AutomationPayload, AutomationStats } from "../../types";

export type AutomationDraft = AutomationPayload &
  Partial<Pick<Automation, "id" | "last_run_at" | "next_run_at" | "created_at" | "updated_at">>;

// --- 定点触发 ---

export type FixedMode = "daily" | "weekly" | "monthly";

export interface FixedScheduleParts {
  mode: FixedMode;
  time: string;
  weekday?: string;
  day?: string;
}

/** 判断 schedule 是否属于定点触发（daily/weekly/monthly cron），并解析出子模式 */
export const parseFixedParts = (
  scheduleType: string,
  scheduleValue: string,
): FixedScheduleParts | null => {
  if (scheduleType === "daily") {
    return { mode: "daily", time: scheduleValue || "09:00" };
  }
  if (scheduleType === "weekly") {
    const { weekday, time } = getWeeklyParts(scheduleValue);
    return { mode: "weekly", time, weekday };
  }
  if (scheduleType === "cron") {
    // 匹配 "0 9 5 * *" 或 "0 09 5 * *" 形式（纯月定时 cron）
    const match = scheduleValue.match(/^0\s+(\d{1,2})\s+(\d{1,2})\s+\*\s+\*$/);
    if (match) {
      const minute = 0;
      const hour = parseInt(match[1], 10);
      const day = match[2];
      const time = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
      return { mode: "monthly", time, day };
    }
  }
  return null;
};

/** 将定点触发子模式构建为后端需要的 schedule_type + schedule_value */
export const buildFixedSchedule = (
  mode: FixedMode,
  time: string,
  weekday?: string,
  day?: string,
): { schedule_type: string; schedule_value: string } => {
  if (mode === "daily") {
    return { schedule_type: "daily", schedule_value: time };
  }
  if (mode === "weekly") {
    return { schedule_type: "weekly", schedule_value: `${weekday ?? "0"}|${time}` };
  }
  // monthly → cron 表达式 "0 {hour} {day} * *"
  const [hourText = "9", minuteText = "0"] = time.split(":");
  const dayNum = day ?? "1";
  return { schedule_type: "cron", schedule_value: `0 ${parseInt(hourText, 10)} ${parseInt(dayNum, 10)} * *` };
};

export const WEEKDAY_OPTIONS = [
  { value: "0", label: "周一" },
  { value: "1", label: "周二" },
  { value: "2", label: "周三" },
  { value: "3", label: "周四" },
  { value: "4", label: "周五" },
  { value: "5", label: "周六" },
  { value: "6", label: "周日" },
];

export const TIMEZONE_SUGGESTIONS = [
  "Asia/Shanghai",
  "UTC",
  "Asia/Tokyo",
  "America/Los_Angeles",
  "Europe/London",
];

export const guessTimezone = () => "Asia/Shanghai";

export const normalizeConversationTitle = (title: string) => {
  if (!title || title === "New Chat") return "新会话";
  return title;
};

export const getDefaultAutomationPayload = (conversationId?: number): AutomationPayload => ({
  name: "新自动化任务",
  conversation_id: conversationId,
  prompt: "总结最近进展，并给出当前最值得执行的下一步建议。",
  schedule_type: "interval",
  schedule_value: "60",
  timezone: guessTimezone(),
  enabled: true,
});

export const formatDateTime = (value?: string | null) => {
  if (!value) return "未设置";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
};

export const formatRelative = (value?: string | null) => {
  if (!value) return "暂无";
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return value;
  const deltaMinutes = Math.round((timestamp - Date.now()) / 60000);
  if (Math.abs(deltaMinutes) < 1) return "刚刚";
  if (Math.abs(deltaMinutes) < 60)
    return deltaMinutes > 0 ? `${deltaMinutes} 分钟后` : `${Math.abs(deltaMinutes)} 分钟前`;
  const deltaHours = Math.round(deltaMinutes / 60);
  if (Math.abs(deltaHours) < 24)
    return deltaHours > 0 ? `${deltaHours} 小时后` : `${Math.abs(deltaHours)} 小时前`;
  const deltaDays = Math.round(deltaHours / 24);
  return deltaDays > 0 ? `${deltaDays} 天后` : `${Math.abs(deltaDays)} 天前`;
};

export const getIntervalParts = (scheduleValue: string) => {
  const minutes = Number.parseInt(scheduleValue, 10);
  if (!Number.isFinite(minutes) || minutes <= 0) {
    return { amount: "60", unit: "minutes" as const };
  }
  if (minutes % 1440 === 0) return { amount: String(minutes / 1440), unit: "days" as const };
  if (minutes % 60 === 0) return { amount: String(minutes / 60), unit: "hours" as const };
  return { amount: String(minutes), unit: "minutes" as const };
};

export const buildIntervalValue = (amountText: string, unit: string) => {
  const amount = Math.max(Number.parseInt(amountText || "0", 10) || 0, 1);
  if (unit === "days") return String(amount * 1440);
  if (unit === "hours") return String(amount * 60);
  return String(amount);
};

export const getWeeklyParts = (scheduleValue: string) => {
  const [weekday = "0", time = "09:00"] = scheduleValue.split("|");
  return { weekday, time };
};

export const getOnceInputValue = (scheduleValue: string) => {
  const date = new Date(scheduleValue);
  if (Number.isNaN(date.getTime())) return "";
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
};

export const buildOnceValue = (localValue: string, timezone: string) => {
  if (!localValue) return "";
  if (timezone === "UTC") return `${localValue}:00Z`;
  return localValue;
};

export const formatSchedule = (
  automation: Pick<AutomationDraft, "schedule_type" | "schedule_value">,
) => {
  if (automation.schedule_type === "once") return `单次 · ${formatDateTime(automation.schedule_value)}`;
  if (automation.schedule_type === "interval") {
    const { amount, unit } = getIntervalParts(automation.schedule_value);
    const unitLabel = unit === "days" ? "天" : unit === "hours" ? "小时" : "分钟";
    return `每 ${amount} ${unitLabel}`;
  }
  if (automation.schedule_type === "daily") return `每天 ${automation.schedule_value}`;
  if (automation.schedule_type === "weekly") {
    const { weekday, time } = getWeeklyParts(automation.schedule_value);
    const weekdayLabel = WEEKDAY_OPTIONS.find((item) => item.value === weekday)?.label ?? weekday;
    return `${weekdayLabel} ${time}`;
  }
  // 检查是否为月定时 cron
  const fixed = parseFixedParts(automation.schedule_type, automation.schedule_value);
  if (fixed?.mode === "monthly") {
    return `每月 ${fixed.day} 号 ${fixed.time}`;
  }
  return `Cron · ${automation.schedule_value}`;
};

export const formatRunStatus = (status: string) => {
  if (status === "success") return "成功";
  if (status === "failed") return "失败";
  if (status === "running") return "执行中";
  if (status === "pending") return "等待中";
  return status;
};

export const getRunTone = (status: string): "success" | "danger" | "warning" | "neutral" => {
  if (status === "success") return "success";
  if (status === "failed") return "danger";
  if (status === "running") return "warning";
  return "neutral";
};

export const summaryCards = (stats: AutomationStats) => [
  {
    label: "总任务数",
    value: stats.total,
    hint: `${stats.enabled} 启用 / ${stats.disabled} 停用`,
  },
  {
    label: "执行中",
    value: stats.running,
    hint: stats.due_now > 0 ? `${stats.due_now} 个任务到点` : "暂无待执行任务",
  },
  {
    label: "最近失败",
    value: stats.failed_recently,
    hint: stats.last_run_at ? `最近执行 ${formatRelative(stats.last_run_at)}` : "暂无运行记录",
  },
  {
    label: "下一次调度",
    value: stats.next_run_at ? formatRelative(stats.next_run_at) : "暂无",
    hint: stats.next_run_at ? formatDateTime(stats.next_run_at) : "没有未来任务",
  },
];
