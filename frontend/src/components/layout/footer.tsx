"use client";

import Link from "next/link";
import Image from "next/image";
import { Mail, Phone, MapPin, ArrowUpRight } from "lucide-react";

const footerLinks = {
  company: [
    { label: "About Us", href: "/about" },
    { label: "Careers", href: "/careers" },
    { label: "Press", href: "/press" },
    { label: "Blog", href: "/blog" },
  ],
  support: [
    { label: "Help Center", href: "/help" },
    { label: "Contact Us", href: "/contact" },
    { label: "FAQs", href: "/faqs" },
    { label: "Refund Policy", href: "/refund-policy" },
  ],
  legal: [
    { label: "Terms of Service", href: "/terms" },
    { label: "Privacy Policy", href: "/privacy" },
    { label: "Cookie Policy", href: "/cookies" },
  ],
};

const socialLinks = [
  { label: "Twitter", href: "https://twitter.com/zoniq" },
  { label: "Instagram", href: "https://instagram.com/zoniq" },
  { label: "YouTube", href: "https://youtube.com/zoniq" },
];

export function Footer() {
  return (
    <footer className="relative border-t border-border/50 bg-background-soft">
      {/* Ambient glow at top */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

      <div className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-2 lg:grid-cols-12">
          {/* Brand — takes 5 cols */}
          <div className="lg:col-span-5">
            <Link href="/" className="inline-flex items-center mb-6 group">
              <Image src="/zoniq-logo.png" alt="ZONIQ" width={120} height={40} className="h-8 w-auto transition-transform duration-300 group-hover:scale-105" />
            </Link>
            <p className="text-sm text-foreground-muted leading-relaxed mb-8 max-w-sm">
              Fair access to the events you love. No bots, no scalpers — just a
              transparent ticketing platform built for real fans.
            </p>
            <div className="space-y-3">
              {[
                { icon: Mail, text: "support@zoniq.in" },
                { icon: Phone, text: "+91 98765 43210" },
                { icon: MapPin, text: "Mumbai, India" },
              ].map((item) => (
                <div key={item.text} className="flex items-center gap-3 text-sm text-foreground-subtle hover:text-foreground-muted transition-colors">
                  <item.icon className="h-4 w-4 text-primary/60" />
                  <span>{item.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Links columns — each 2 cols, spaced with gap */}
          {[
            { title: "Company", links: footerLinks.company },
            { title: "Support", links: footerLinks.support },
            { title: "Legal", links: footerLinks.legal },
          ].map((section) => (
            <div key={section.title} className="lg:col-span-2">
              <h3 className="text-[11px] font-bold text-foreground-subtle uppercase tracking-widest mb-5">
                {section.title}
              </h3>
              <ul className="space-y-3">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-foreground-muted hover:text-foreground transition-colors duration-200"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-16 pt-8 border-t border-border/50 flex flex-col md:flex-row items-center justify-between gap-6">
          <p className="text-xs text-foreground-subtle">
            &copy; {new Date().getFullYear()} ZONIQ. All rights reserved.
          </p>

          {/* Social Links */}
          <div className="flex items-center gap-5">
            {socialLinks.map((social) => (
              <a
                key={social.label}
                href={social.href}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-1 text-xs text-foreground-subtle hover:text-foreground transition-colors duration-200"
                aria-label={social.label}
              >
                {social.label}
                <ArrowUpRight className="h-3 w-3 opacity-0 -translate-y-0.5 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-200" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
