"use client";

import * as React from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { motion, AnimatePresence } from "framer-motion";
import { HoverButton } from "@/components/ui/hover-button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2 } from "lucide-react";
import { login as apiLogin, register as apiRegister } from "@/services/api";

export type AuthView = "login" | "register" | "reset";

// Validation schemas
const loginSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email." }),
  password: z.string().min(1, { message: "Password is required." }),
  rememberMe: z.boolean().default(false).optional(),
});

const registerSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters." }),
  email: z.string().email({ message: "Please enter a valid email." }),
  password: z.string().min(8, { message: "Password must be at least 8 characters." }),
});

const resetSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email." }),
});

interface AuthSplitScreenProps {
  logo: React.ReactNode;
  imageSrc: string;
  imageAlt: string;
}

export function AuthSplitScreen({ logo, imageSrc, imageAlt }: AuthSplitScreenProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialView = (searchParams.get("view") as AuthView) || "login";
  
  const [view, setView] = React.useState<AuthView>(initialView);
  const [isLoading, setIsLoading] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState("");
  const [resetSuccess, setResetSuccess] = React.useState(false);

  const loginForm = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", rememberMe: false },
  });

  const registerForm = useForm<z.infer<typeof registerSchema>>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "", password: "" },
  });

  const resetForm = useForm<z.infer<typeof resetSchema>>({
    resolver: zodResolver(resetSchema),
    defaultValues: { email: "" },
  });

  const onLogin = async (data: z.infer<typeof loginSchema>) => {
    setIsLoading(true);
    setErrorMsg("");
    try {
      await apiLogin(data.email, data.password);
      router.push("/dashboard");
    } catch (err: any) {
      setErrorMsg(err.message || "Login failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const onRegister = async (data: z.infer<typeof registerSchema>) => {
    setIsLoading(true);
    setErrorMsg("");
    try {
      await apiRegister(data.name, data.email, data.password);
      router.push("/dashboard");
    } catch (err: any) {
      setErrorMsg(err.message || "Registration failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const onReset = async (data: z.infer<typeof resetSchema>) => {
    setIsLoading(true);
    setErrorMsg("");
    setResetSuccess(false);
    try {
      const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4000";
      const res = await fetch(`${API}/api/auth/forgotpassword`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: data.email }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "Request failed.");
      setResetSuccess(true);
    } catch (err: any) {
      setErrorMsg(err.message || "Could not send reset email.");
    } finally {
      setIsLoading(false);
    }
  };

  // Animation variants
  const slideVariants = {
    initial: { opacity: 0, x: -20 },
    enter: { opacity: 1, x: 0, transition: { duration: 0.3, staggerChildren: 0.1 } },
    exit: { opacity: 0, x: 20, transition: { duration: 0.2 } },
  };

  const itemVariants = {
    initial: { opacity: 0, y: 10 },
    enter: { opacity: 1, y: 0 },
  };

  return (
    <div className="relative flex min-h-screen w-full flex-col md:flex-row z-10">
      {/* Left Panel: Forms */}
      <div className="flex w-full flex-col items-center justify-center p-8 md:w-1/2 min-h-screen">
        <div className="w-full max-w-md relative">
          <div className="mb-8">{logo}</div>
          
          <AnimatePresence mode="wait">
            {view === "login" && (
              <motion.div
                key="login"
                variants={slideVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="flex flex-col gap-6"
              >
                <div className="text-left">
                  <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Welcome Back</h1>
                  <p className="text-sm text-white/50">Sign in to your account to continue</p>
                  {errorMsg && view === "login" && (
                    <p className="mt-2 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{errorMsg}</p>
                  )}
                </div>

                <Form {...loginForm}>
                  <form onSubmit={loginForm.handleSubmit(onLogin)} className="space-y-4">
                    <FormField
                      control={loginForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-white/80">Email Address</FormLabel>
                          <FormControl>
                            <Input placeholder="email@example.com" {...field} disabled={isLoading} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={loginForm.control}
                      name="password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-white/80">Password</FormLabel>
                          <FormControl>
                            <Input type="password" placeholder="••••••••••••" {...field} disabled={isLoading} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="flex items-center justify-between pt-2">
                      <FormField
                        control={loginForm.control}
                        name="rememberMe"
                        render={({ field }) => (
                          <FormItem className="flex flex-row items-center space-x-3 space-y-0">
                            <FormControl>
                              <Checkbox checked={field.value} onCheckedChange={field.onChange} disabled={isLoading} />
                            </FormControl>
                            <FormLabel className="font-normal text-white/60 cursor-pointer">Remember me</FormLabel>
                          </FormItem>
                        )}
                      />
                      <button
                        type="button"
                        onClick={() => setView("reset")}
                        className="relative text-sm font-medium text-indigo-400 hover:text-indigo-300 transition-colors group"
                      >
                        Forgot password?
                        <span className="absolute -bottom-1 left-0 w-0 h-[1px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                      </button>
                    </div>

                    <HoverButton type="submit" className="w-full mt-4" disabled={isLoading}>
                      {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin inline" /> : null}
                      Sign In
                    </HoverButton>
                  </form>
                </Form>

                <p className="text-center text-sm text-white/50 mt-4">
                  Don't have an account?{" "}
                  <button 
                    onClick={() => setView("register")} 
                    className="relative font-medium text-indigo-400 hover:text-indigo-300 transition-colors group"
                  >
                    Create one here
                    <span className="absolute -bottom-1 left-0 w-0 h-[1px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                  </button>
                </p>
              </motion.div>
            )}

            {view === "register" && (
              <motion.div
                key="register"
                variants={slideVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="flex flex-col gap-6"
              >
                <div className="text-left">
                  <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Create an Account</h1>
                  <p className="text-sm text-white/50">Join us to start finding the perfect candidates</p>
                  {errorMsg && view === "register" && (
                    <p className="mt-2 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{errorMsg}</p>
                  )}
                </div>

                <Form {...registerForm}>
                  <form onSubmit={registerForm.handleSubmit(onRegister)} className="space-y-4">
                    <FormField
                      control={registerForm.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-white/80">Full Name</FormLabel>
                          <FormControl>
                            <Input placeholder="John Doe" {...field} disabled={isLoading} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={registerForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-white/80">Email Address</FormLabel>
                          <FormControl>
                            <Input placeholder="email@example.com" {...field} disabled={isLoading} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={registerForm.control}
                      name="password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-white/80">Password</FormLabel>
                          <FormControl>
                            <Input type="password" placeholder="••••••••••••" {...field} disabled={isLoading} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <HoverButton type="submit" className="w-full mt-4" disabled={isLoading}>
                      {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin inline" /> : null}
                      Sign Up
                    </HoverButton>
                  </form>
                </Form>

                <p className="text-center text-sm text-white/50 mt-4">
                  Already have an account?{" "}
                  <button 
                    onClick={() => setView("login")} 
                    className="relative font-medium text-indigo-400 hover:text-indigo-300 transition-colors group"
                  >
                    Sign in here
                    <span className="absolute -bottom-1 left-0 w-0 h-[1px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                  </button>
                </p>
              </motion.div>
            )}

            {view === "reset" && (
              <motion.div
                key="reset"
                variants={slideVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="flex flex-col gap-6"
              >
                <div className="text-left">
                  <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Reset Password</h1>
                  <p className="text-sm text-white/50">Enter your email and we'll send you a recovery link</p>
                </div>

                {resetSuccess ? (
                  <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 px-4 py-5 text-center space-y-2">
                    <p className="text-emerald-400 font-semibold">Check your inbox! ✓</p>
                    <p className="text-sm text-white/50">A password reset link has been sent to your email address. It expires in 10 minutes.</p>
                    <button
                      onClick={() => { setResetSuccess(false); setView("login"); }}
                      className="mt-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      Back to Sign in
                    </button>
                  </div>
                ) : (
                  <>
                    {errorMsg && view === "reset" && (
                      <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{errorMsg}</p>
                    )}
                    <Form {...resetForm}>
                      <form onSubmit={resetForm.handleSubmit(onReset)} className="space-y-4">
                        <FormField
                          control={resetForm.control}
                          name="email"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className="text-white/80">Email Address</FormLabel>
                              <FormControl>
                                <Input placeholder="email@example.com" {...field} disabled={isLoading} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        <HoverButton type="submit" className="w-full mt-4" disabled={isLoading}>
                          {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin inline" /> : null}
                          Send Recovery Link
                        </HoverButton>
                      </form>
                    </Form>
                    <p className="text-center text-sm text-white/50 mt-4">
                      Remember your password?{" "}
                      <button
                        onClick={() => { setView("login"); setErrorMsg(""); }}
                        className="relative font-medium text-indigo-400 hover:text-indigo-300 transition-colors group"
                      >
                        Back to Sign in
                        <span className="absolute -bottom-1 left-0 w-0 h-[1px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                      </button>
                    </p>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Right Panel: Image */}
      <div className="relative hidden w-1/2 md:block overflow-hidden border-l border-white/[0.05]">
        <div className="absolute inset-0 bg-indigo-500/10 mix-blend-multiply z-10" />
        <img
          src={imageSrc}
          alt={imageAlt}
          className="h-full w-full object-cover grayscale opacity-60"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#030303] via-transparent to-transparent z-20" />
        <div className="absolute inset-0 bg-gradient-to-l from-transparent to-[#030303] z-20" />
      </div>
    </div>
  );
}
