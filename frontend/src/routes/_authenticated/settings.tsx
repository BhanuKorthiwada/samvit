import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import {
  Bell,
  Check,
  Globe,
  Monitor,
  Moon,
  Palette,
  Sun,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useTheme } from '@/contexts/ThemeContext';

export const Route = createFileRoute('/_authenticated/settings')({
  component: SettingsPage,
});

function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [leaveApprovalNotifications, setLeaveApprovalNotifications] = useState(true);
  const [attendanceReminders, setAttendanceReminders] = useState(true);
  const [payslipNotifications, setPayslipNotifications] = useState(true);
  const [language, setLanguage] = useState('en');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [success, setSuccess] = useState('');

  const handleSave = () => {
    // TODO: Save settings to backend
    setSuccess('Settings saved successfully');
    setTimeout(() => setSuccess(''), 3000);
  };

  const themes = [
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'system', label: 'System', icon: Monitor },
  ] as const;

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'hi', label: 'Hindi' },
    { value: 'ta', label: 'Tamil' },
    { value: 'te', label: 'Telugu' },
    { value: 'kn', label: 'Kannada' },
  ];

  const timezones = [
    { value: 'Asia/Kolkata', label: 'India (IST)' },
    { value: 'America/New_York', label: 'Eastern Time (ET)' },
    { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
    { value: 'Europe/London', label: 'London (GMT)' },
    { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
  ];

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">Manage your preferences and notifications</p>
      </div>

      {success && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center gap-2 text-green-400">
          <Check className="w-4 h-4" />
          <span className="text-sm">{success}</span>
        </div>
      )}

      {/* Appearance */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Palette className="w-5 h-5 text-cyan-400" />
            <CardTitle className="text-white">Appearance</CardTitle>
          </div>
          <CardDescription>Customize how the application looks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label className="text-sm font-medium text-slate-300">Theme</Label>
            <div className="grid grid-cols-3 gap-3 mt-3">
              {themes.map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  onClick={() => setTheme(value)}
                  className={`flex flex-col items-center gap-2 p-4 rounded-lg border transition-all ${
                    theme === value
                      ? 'border-cyan-500 bg-cyan-500/10'
                      : 'border-slate-600 bg-slate-700/30 hover:border-slate-500'
                  }`}
                >
                  <Icon className={`w-6 h-6 ${theme === value ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span className={`text-sm ${theme === value ? 'text-cyan-400' : 'text-slate-300'}`}>
                    {label}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Localization */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-cyan-400" />
            <CardTitle className="text-white">Localization</CardTitle>
          </div>
          <CardDescription>Set your language and timezone preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="language">Language</Label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="mt-1.5 w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white"
              >
                {languages.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="timezone">Timezone</Label>
              <select
                id="timezone"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="mt-1.5 w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white"
              >
                {timezones.map((tz) => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-cyan-400" />
            <CardTitle className="text-white">Notifications</CardTitle>
          </div>
          <CardDescription>Choose what notifications you want to receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Email Notifications</p>
              <p className="text-sm text-slate-400">Receive notifications via email</p>
            </div>
            <Switch
              checked={emailNotifications}
              onCheckedChange={setEmailNotifications}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Leave Approval Alerts</p>
              <p className="text-sm text-slate-400">Get notified when leaves are approved or rejected</p>
            </div>
            <Switch
              checked={leaveApprovalNotifications}
              onCheckedChange={setLeaveApprovalNotifications}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Attendance Reminders</p>
              <p className="text-sm text-slate-400">Daily reminders to clock in and out</p>
            </div>
            <Switch
              checked={attendanceReminders}
              onCheckedChange={setAttendanceReminders}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Payslip Notifications</p>
              <p className="text-sm text-slate-400">Get notified when new payslips are available</p>
            </div>
            <Switch
              checked={payslipNotifications}
              onCheckedChange={setPayslipNotifications}
            />
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave}>Save Settings</Button>
      </div>
    </div>
  );
}
