import { Link, createFileRoute, redirect, useNavigate } from '@tanstack/react-router';
import { useState } from 'react';
import {
  AlertCircle,
  ArrowLeft,
  Building2,
  CheckCircle2,
  Globe,
  Loader2,
  Lock,
  Mail,
  Phone,
  User,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { authService } from '@/lib/api';

export const Route = createFileRoute('/signup')({
  beforeLoad: () => {
    // If already authenticated, redirect to dashboard
    if (localStorage.getItem('access_token')) {
      throw redirect({ to: '/dashboard' });
    }
  },
  component: SignupPage,
});

type Step = 'company' | 'admin' | 'success';

interface SignupFormData {
  // Company info
  company_name: string;
  domain: string;
  company_email: string;
  company_phone: string;
  // Admin user info
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

function SignupPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('company');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<SignupFormData>({
    company_name: '',
    domain: '',
    company_email: '',
    company_phone: '',
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  });

  const baseDomain = 'samvit.bhanu.dev';

  const updateField = (field: keyof SignupFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const generateDomain = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 20);
  };

  const handleCompanyNameChange = (value: string) => {
    updateField('company_name', value);
    if (!formData.domain || formData.domain === generateDomain(formData.company_name)) {
      updateField('domain', generateDomain(value));
    }
  };

  const validateCompanyStep = (): boolean => {
    if (!formData.company_name.trim()) {
      setError('Company name is required');
      return false;
    }
    if (!formData.domain.trim()) {
      setError('Subdomain is required');
      return false;
    }
    if (!/^[a-z0-9-]+$/.test(formData.domain)) {
      setError('Subdomain can only contain lowercase letters, numbers, and hyphens');
      return false;
    }
    if (!formData.company_email.trim()) {
      setError('Company email is required');
      return false;
    }
    return true;
  };

  const validateAdminStep = (): boolean => {
    if (!formData.first_name.trim()) {
      setError('First name is required');
      return false;
    }
    if (!formData.last_name.trim()) {
      setError('Last name is required');
      return false;
    }
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return false;
    }
    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match');
      return false;
    }
    return true;
  };

  const handleNextStep = () => {
    setError('');
    if (step === 'company' && validateCompanyStep()) {
      setStep('admin');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateAdminStep()) {
      return;
    }

    setIsLoading(true);

    try {
      await authService.registerCompany({
        company_name: formData.company_name,
        subdomain: formData.domain,
        company_email: formData.company_email,
        company_phone: formData.company_phone || undefined,
        admin_email: formData.email,
        admin_password: formData.password,
        admin_first_name: formData.first_name,
        admin_last_name: formData.last_name,
      });

      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (step === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
        <Card className="w-full max-w-md bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/10 mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Account Created!</h2>
              <p className="text-slate-400 mb-6">
                Your company account has been created successfully. You can now access your HRMS at:
              </p>
              <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
                <p className="text-cyan-400 font-mono text-lg">
                  {formData.domain}.{baseDomain}
                </p>
              </div>
              <p className="text-sm text-slate-500 mb-6">
                We&apos;ve sent a verification email to <strong>{formData.email}</strong>
              </p>
              <Button
                onClick={() => navigate({ to: '/login' })}
                className="w-full"
              >
                Go to Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <div className="w-full max-w-lg">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-500/10 mb-4">
            <Building2 className="w-8 h-8 text-cyan-400" />
          </div>
          <h1 className="text-3xl font-bold text-white">Create Your Account</h1>
          <p className="text-slate-400 mt-2">
            Set up your company&apos;s HRMS in minutes
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step === 'company'
                  ? 'bg-cyan-500 text-white'
                  : 'bg-cyan-500/20 text-cyan-400'
                }`}
            >
              1
            </div>
            <span className="text-sm text-slate-400 hidden sm:inline">Company Info</span>
          </div>
          <div className="w-12 h-0.5 bg-slate-700" />
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step === 'admin'
                  ? 'bg-cyan-500 text-white'
                  : 'bg-slate-700 text-slate-400'
                }`}
            >
              2
            </div>
            <span className="text-sm text-slate-400 hidden sm:inline">Admin Account</span>
          </div>
        </div>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">
              {step === 'company' ? 'Company Information' : 'Admin Account'}
            </CardTitle>
            <CardDescription>
              {step === 'company'
                ? 'Enter your company details to get started'
                : 'Create your administrator account'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-400">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <form onSubmit={step === 'admin' ? handleSubmit : (e) => { e.preventDefault(); handleNextStep(); }}>
              {step === 'company' && (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="company_name">Company Name</Label>
                    <div className="relative mt-1.5">
                      <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="company_name"
                        type="text"
                        value={formData.company_name}
                        onChange={(e) => handleCompanyNameChange(e.target.value)}
                        placeholder="Acme Corporation"
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="domain">Subdomain</Label>
                    <div className="relative mt-1.5">
                      <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="domain"
                        type="text"
                        value={formData.domain}
                        onChange={(e) => updateField('domain', e.target.value.toLowerCase())}
                        placeholder="acme"
                        className="pl-10"
                        required
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1.5">
                      Your HRMS will be available at{' '}
                      <span className="text-cyan-400">
                        {formData.domain || 'subdomain'}.{baseDomain}
                      </span>
                    </p>
                  </div>

                  <div>
                    <Label htmlFor="company_email">Company Email</Label>
                    <div className="relative mt-1.5">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="company_email"
                        type="email"
                        value={formData.company_email}
                        onChange={(e) => updateField('company_email', e.target.value)}
                        placeholder="hr@acme.com"
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="company_phone">Phone Number (Optional)</Label>
                    <div className="relative mt-1.5">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="company_phone"
                        type="tel"
                        value={formData.company_phone}
                        onChange={(e) => updateField('company_phone', e.target.value)}
                        placeholder="+91 98765 43210"
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <Button type="submit" className="w-full mt-6">
                    Continue
                  </Button>
                </div>
              )}

              {step === 'admin' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="first_name">First Name</Label>
                      <div className="relative mt-1.5">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <Input
                          id="first_name"
                          type="text"
                          value={formData.first_name}
                          onChange={(e) => updateField('first_name', e.target.value)}
                          placeholder="John"
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="last_name">Last Name</Label>
                      <Input
                        id="last_name"
                        type="text"
                        value={formData.last_name}
                        onChange={(e) => updateField('last_name', e.target.value)}
                        placeholder="Doe"
                        className="mt-1.5"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="email">Admin Email</Label>
                    <div className="relative mt-1.5">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => updateField('email', e.target.value)}
                        placeholder="john.doe@acme.com"
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="password">Password</Label>
                    <div className="relative mt-1.5">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="password"
                        type="password"
                        value={formData.password}
                        onChange={(e) => updateField('password', e.target.value)}
                        placeholder="••••••••"
                        className="pl-10"
                        minLength={8}
                        required
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1.5">
                      Must be at least 8 characters
                    </p>
                  </div>

                  <div>
                    <Label htmlFor="confirm_password">Confirm Password</Label>
                    <div className="relative mt-1.5">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="confirm_password"
                        type="password"
                        value={formData.confirm_password}
                        onChange={(e) => updateField('confirm_password', e.target.value)}
                        placeholder="••••••••"
                        className="pl-10"
                        minLength={8}
                        required
                      />
                    </div>
                  </div>

                  <div className="flex gap-3 mt-6">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => { setError(''); setStep('company'); }}
                      className="flex-1"
                    >
                      <ArrowLeft className="w-4 h-4 mr-2" />
                      Back
                    </Button>
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="flex-1"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        'Create Account'
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-slate-400">
                Already have an account?{' '}
                <Link to="/login" className="text-cyan-400 hover:text-cyan-300 transition-colors">
                  Sign in
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-slate-500 text-sm mt-6">
          © 2024 SAMVIT HRMS. All rights reserved.
        </p>
      </div>
    </div>
  );
}
