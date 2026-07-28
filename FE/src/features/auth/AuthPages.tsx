import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowRight,
  Check,
  Eye,
  EyeSlash,
  ShieldCheck,
  Sparkle,
} from "@phosphor-icons/react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Button, Input, StatusMessage } from "../../components/ui";
import { ApiError, authApi } from "../../lib/api";
import { useAuth } from "./AuthProvider";

const loginSchema = z.object({
  username: z.string().trim().min(1, "Enter your username."),
  password: z.string().min(1, "Enter your password."),
});

const registerSchema = z
  .object({
    full_name: z.string().trim().max(100).optional(),
    username: z
      .string()
      .trim()
      .min(3, "Use at least 3 characters.")
      .max(50, "Use no more than 50 characters.")
      .regex(
        /^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/,
        "Start with a letter or number; use only letters, numbers, ., _ or -.",
      ),
    email: z.email("Enter a valid email address."),
    password: z
      .string()
      .min(8, "Use at least 8 characters.")
      .max(128, "Use no more than 128 characters."),
    password_confirm: z.string(),
  })
  .refine((values) => values.password === values.password_confirm, {
    path: ["password_confirm"],
    message: "Passwords do not match.",
  });

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;

function AuthLayout({
  children,
  title,
  description,
}: {
  children: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <main className="auth-layout">
      <section className="auth-story" aria-label="LexiLoop introduction">
        <Link to="/" className="brand brand--auth">
          <img src="/lexiloop-mark.svg" alt="" />
          <span>LexiLoop</span>
        </Link>
        <div className="auth-story__content">
          <p className="eyebrow eyebrow--light">Learn in context</p>
          <h1>Build vocabulary you can actually use.</h1>
          <p>
            Organize every meaning, collocation and example. Turn saved words
            into lasting knowledge, one thoughtful loop at a time.
          </p>
          <ul>
            <li>
              <Sparkle aria-hidden weight="fill" />
              Rich vocabulary, beyond simple translations
            </li>
            <li>
              <ShieldCheck aria-hidden weight="fill" />
              Private decks by default
            </li>
            <li>
              <Check aria-hidden weight="bold" />
              A focused experience designed for students
            </li>
          </ul>
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-card__heading">
            <p className="eyebrow">Welcome to LexiLoop</p>
            <h2>{title}</h2>
            <p>{description}</p>
          </div>
          {children}
        </div>
      </section>
    </main>
  );
}

export function LoginPage() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  if (user) return <Navigate to="/" replace />;

  const onSubmit = handleSubmit(async (values) => {
    setServerError("");
    try {
      await signIn(values.username, values.password);
      const target =
        (location.state as { from?: string } | null)?.from ?? "/";
      navigate(target, { replace: true });
    } catch (error) {
      setServerError(
        error instanceof ApiError
          ? error.message
          : "Sign in failed. Please try again.",
      );
    }
  });

  return (
    <AuthLayout
      title="Sign in"
      description="Continue building your personal language library."
    >
      <form className="form-stack" onSubmit={onSubmit} noValidate>
        {serverError ? (
          <StatusMessage tone="error">{serverError}</StatusMessage>
        ) : null}
        <Input
          label="Username"
          autoComplete="username"
          autoFocus
          error={errors.username?.message}
          {...register("username")}
        />
        <div className="password-field">
          <Input
            label="Password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            error={errors.password?.message}
            {...register("password")}
          />
          <button
            type="button"
            className="password-field__toggle"
            onClick={() => setShowPassword((value) => !value)}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeSlash aria-hidden /> : <Eye aria-hidden />}
          </button>
        </div>
        <Button type="submit" isLoading={isSubmitting}>
          Sign in <ArrowRight aria-hidden size={18} />
        </Button>
      </form>
      <p className="auth-card__switch">
        New to LexiLoop? <Link to="/register">Create an account</Link>
      </p>
    </AuthLayout>
  );
}

export function RegisterPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      username: "",
      email: "",
      password: "",
      password_confirm: "",
    },
  });

  if (user) return <Navigate to="/" replace />;

  const onSubmit = handleSubmit(async (values) => {
    setServerError("");
    try {
      await authApi.register({
        ...values,
        full_name: values.full_name || null,
      });
      navigate("/login", {
        replace: true,
        state: { registrationComplete: true },
      });
    } catch (error) {
      setServerError(
        error instanceof ApiError
          ? error.message
          : "Your account could not be created.",
      );
    }
  });

  return (
    <AuthLayout
      title="Create your account"
      description="Start with your first deck and grow from there."
    >
      <form className="form-stack" onSubmit={onSubmit} noValidate>
        {serverError ? (
          <StatusMessage tone="error">{serverError}</StatusMessage>
        ) : null}
        <Input
          label="Full name"
          optional
          autoComplete="name"
          error={errors.full_name?.message}
          {...register("full_name")}
        />
        <Input
          label="Username"
          autoComplete="username"
          error={errors.username?.message}
          {...register("username")}
        />
        <Input
          label="Email"
          type="email"
          inputMode="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register("email")}
        />
        <div className="form-grid form-grid--two">
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register("password")}
          />
          <Input
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            error={errors.password_confirm?.message}
            {...register("password_confirm")}
          />
        </div>
        <Button type="submit" isLoading={isSubmitting}>
          Create account <ArrowRight aria-hidden size={18} />
        </Button>
      </form>
      <p className="auth-card__switch">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </AuthLayout>
  );
}
