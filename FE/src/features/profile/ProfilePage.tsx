import { zodResolver } from "@hookform/resolvers/zod";
import {
  IdentificationCard,
  LockKey,
  SignOut,
  Trash,
  UserCircle,
} from "@phosphor-icons/react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import {
  Button,
  ConfirmDialog,
  Input,
  PageHeader,
  StatusMessage,
} from "../../components/ui";
import { useAuth } from "../auth/AuthProvider";
import { ApiError, authApi, userApi } from "../../lib/api";

const profileSchema = z.object({
  full_name: z.string().trim().max(100).optional(),
  username: z
    .string()
    .trim()
    .min(3, "Use at least 3 characters.")
    .max(50)
    .regex(/^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/, "Use a valid username."),
  email: z.email("Enter a valid email address."),
  phone: z
    .string()
    .trim()
    .regex(/^\+?[1-9]\d{1,14}$/, "Use an international phone number.")
    .or(z.literal(""))
    .optional(),
  avatar_url: z.url("Enter a valid URL.").or(z.literal("")).optional(),
});

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Enter your current password."),
    new_password: z.string().min(8, "Use at least 8 characters.").max(128),
    new_password_confirm: z.string(),
  })
  .refine((values) => values.new_password === values.new_password_confirm, {
    path: ["new_password_confirm"],
    message: "Passwords do not match.",
  });

type ProfileValues = z.infer<typeof profileSchema>;
type PasswordValues = z.infer<typeof passwordSchema>;

export function ProfilePage() {
  const { user, setUser, signOut } = useAuth();
  const navigate = useNavigate();
  const [profileStatus, setProfileStatus] = useState("");
  const [profileError, setProfileError] = useState("");
  const [passwordStatus, setPasswordStatus] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    values: {
      full_name: user?.full_name ?? "",
      username: user?.username ?? "",
      email: user?.email ?? "",
      phone: user?.phone ?? "",
      avatar_url: user?.avatar_url ?? "",
    },
  });
  const passwordForm = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      new_password_confirm: "",
    },
  });

  const saveProfile = profileForm.handleSubmit(async (values) => {
    setProfileError("");
    setProfileStatus("");
    try {
      const updated = await userApi.update({
        full_name: values.full_name || null,
        username: values.username,
        email: values.email,
        phone: values.phone || null,
        avatar_url: values.avatar_url || null,
      });
      setUser(updated);
      setProfileStatus("Profile changes saved.");
    } catch (error) {
      setProfileError(
        error instanceof ApiError ? error.message : "Profile could not be saved.",
      );
    }
  });

  const changePassword = passwordForm.handleSubmit(async (values) => {
    setPasswordError("");
    setPasswordStatus("");
    try {
      await authApi.changePassword(values);
      passwordForm.reset();
      setPasswordStatus(
        "Password changed. Other refresh sessions have been signed out.",
      );
    } catch (error) {
      setPasswordError(
        error instanceof ApiError
          ? error.message
          : "Password could not be changed.",
      );
    }
  });

  const handleDeleteAccount = async () => {
    await userApi.remove();
    await signOut();
    navigate("/login", { replace: true });
  };

  return (
    <div className="page page--profile">
      <PageHeader
        eyebrow="Account"
        title="Profile and security"
        description="Manage your personal details and protect your account."
      />
      <div className="profile-layout">
        <aside className="profile-summary">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="" className="profile-summary__avatar" />
          ) : (
            <span className="profile-summary__avatar profile-summary__avatar--fallback">
              {(user?.full_name || user?.username || "U")[0]?.toUpperCase()}
            </span>
          )}
          <h2>{user?.full_name || user?.username}</h2>
          <p>@{user?.username}</p>
          <span className="badge badge--primary">{user?.role}</span>
          <div className="profile-summary__meta">
            <span>Member since</span>
            <strong>
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString(undefined, {
                    month: "long",
                    year: "numeric",
                  })
                : "—"}
            </strong>
          </div>
        </aside>

        <div className="profile-sections">
          <section className="surface profile-section">
            <div className="profile-section__heading">
              <IdentificationCard aria-hidden weight="duotone" />
              <div><h2>Personal information</h2><p>Used across your LexiLoop account.</p></div>
            </div>
            <form className="form-stack" onSubmit={saveProfile} noValidate>
              {profileStatus ? <StatusMessage tone="success">{profileStatus}</StatusMessage> : null}
              {profileError ? <StatusMessage tone="error">{profileError}</StatusMessage> : null}
              <div className="form-grid form-grid--two">
                <Input label="Full name" optional error={profileForm.formState.errors.full_name?.message} {...profileForm.register("full_name")} />
                <Input label="Username" error={profileForm.formState.errors.username?.message} {...profileForm.register("username")} />
                <Input label="Email" type="email" inputMode="email" error={profileForm.formState.errors.email?.message} {...profileForm.register("email")} />
                <Input label="Phone" optional inputMode="tel" placeholder="+84912345678" error={profileForm.formState.errors.phone?.message} {...profileForm.register("phone")} />
              </div>
              <Input label="Avatar URL" optional type="url" error={profileForm.formState.errors.avatar_url?.message} {...profileForm.register("avatar_url")} />
              <div className="form-actions"><Button type="submit" isLoading={profileForm.formState.isSubmitting}>Save profile</Button></div>
            </form>
          </section>

          <section className="surface profile-section">
            <div className="profile-section__heading">
              <LockKey aria-hidden weight="duotone" />
              <div><h2>Change password</h2><p>This signs out your other refresh sessions.</p></div>
            </div>
            <form className="form-stack" onSubmit={changePassword} noValidate>
              {passwordStatus ? <StatusMessage tone="success">{passwordStatus}</StatusMessage> : null}
              {passwordError ? <StatusMessage tone="error">{passwordError}</StatusMessage> : null}
              <Input label="Current password" type="password" autoComplete="current-password" error={passwordForm.formState.errors.current_password?.message} {...passwordForm.register("current_password")} />
              <div className="form-grid form-grid--two">
                <Input label="New password" type="password" autoComplete="new-password" error={passwordForm.formState.errors.new_password?.message} {...passwordForm.register("new_password")} />
                <Input label="Confirm new password" type="password" autoComplete="new-password" error={passwordForm.formState.errors.new_password_confirm?.message} {...passwordForm.register("new_password_confirm")} />
              </div>
              <div className="form-actions"><Button type="submit" isLoading={passwordForm.formState.isSubmitting}>Change password</Button></div>
            </form>
          </section>

          <section className="surface profile-section profile-section--danger">
            <div className="profile-section__heading">
              <UserCircle aria-hidden weight="duotone" />
              <div><h2>Account actions</h2><p>Sign out or permanently remove this account.</p></div>
            </div>
            <div className="account-actions">
              <Button variant="secondary" onClick={async () => { await signOut(); navigate("/login"); }}>
                <SignOut aria-hidden /> Sign out
              </Button>
              <ConfirmDialog
                trigger={<Button variant="danger"><Trash aria-hidden /> Delete account</Button>}
                title="Delete your account?"
                description="Your account and active content will no longer be available. This action cannot be reversed in the app."
                confirmLabel="Delete account"
                onConfirm={handleDeleteAccount}
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
