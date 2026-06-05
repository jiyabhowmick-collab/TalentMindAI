import { Globe, MessageSquare, User } from "lucide-react";

export function Footer() {
    return (
        <footer className="w-full bg-[#030303] border-t border-white/[0.05] py-12 px-4 md:px-6">
            <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex flex-col gap-2 text-center md:text-left">
                    <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 to-rose-300">
                        Talent-Mind
                    </span>
                    <p className="text-white/40 text-sm font-light">
                        Intelligent Candidate Ranking Engine.
                    </p>
                </div>
                
                <div className="flex items-center gap-6">
                    <a href="#" className="text-white/40 hover:text-indigo-300 transition-colors">
                        <Globe className="h-5 w-5" />
                        <span className="sr-only">Website</span>
                    </a>
                    <a href="#" className="text-white/40 hover:text-indigo-300 transition-colors">
                        <MessageSquare className="h-5 w-5" />
                        <span className="sr-only">Contact</span>
                    </a>
                    <a href="#" className="text-white/40 hover:text-indigo-300 transition-colors">
                        <User className="h-5 w-5" />
                        <span className="sr-only">Profile</span>
                    </a>
                </div>
            </div>
            
            <div className="max-w-6xl mx-auto mt-12 pt-8 border-t border-white/[0.02] flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-white/30 font-light">
                <p>© {new Date().getFullYear()} hack2skill POC. All rights reserved.</p>
                <div className="flex gap-4">
                    <a href="#" className="hover:text-white/60 transition-colors">Privacy Policy</a>
                    <a href="#" className="hover:text-white/60 transition-colors">Terms of Service</a>
                </div>
            </div>
        </footer>
    );
}
