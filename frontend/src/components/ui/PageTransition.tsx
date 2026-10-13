import React from 'react';
import { motion } from 'framer-motion';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.05,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 18, scale: 0.98 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 380,
      damping: 28,
    },
  },
};

interface PageTransitionProps {
  children: React.ReactNode;
  tabKey: string;
}

/** Wraps a full view — cinematic blur dissolution & silky scale transition on tab switch */
export const PageTransition: React.FC<PageTransitionProps> = ({ children, tabKey }) => {
  return (
    <motion.div
      key={tabKey}
      initial={{ opacity: 0, y: 16, scale: 0.985, filter: 'blur(8px)' }}
      animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
      exit={{ opacity: 0, y: -12, scale: 0.99, filter: 'blur(6px)' }}
      transition={{
        duration: 0.32,
        ease: [0.16, 1, 0.3, 1],
      }}
      className="w-full"
    >
      {children}
    </motion.div>
  );
};

/** Wraps the children container with stagger */
export const StaggerContainer: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <motion.div
    className={`space-y-6 ${className}`}
    variants={containerVariants}
    initial="hidden"
    animate="visible"
  >
    {children}
  </motion.div>
);

/** Wraps each card/section with entrance animation */
export const FadeUp: React.FC<{ children: React.ReactNode; delay?: number; className?: string }> = ({
  children,
  delay = 0,
  className = '',
}) => (
  <motion.div
    className={className}
    variants={itemVariants}
    custom={delay}
  >
    {children}
  </motion.div>
);

/** Standalone fade-up with explicit animation (outside stagger) */
export const FadeIn: React.FC<{
  children: React.ReactNode;
  delay?: number;
  className?: string;
  y?: number;
}> = ({ children, delay = 0, className = '', y = 16 }) => (
  <motion.div
    className={className}
    initial={{ opacity: 0, y }}
    animate={{ opacity: 1, y: 0 }}
    transition={{
      delay,
      type: 'spring',
      stiffness: 380,
      damping: 28,
    }}
  >
    {children}
  </motion.div>
);

/** Scale-in for number KPI tiles */
export const ScaleIn: React.FC<{ children: React.ReactNode; delay?: number }> = ({ children, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.92 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ delay, type: 'spring', stiffness: 500, damping: 30 }}
  >
    {children}
  </motion.div>
);
