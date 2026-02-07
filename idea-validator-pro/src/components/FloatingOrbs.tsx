import { motion } from 'framer-motion';

export function FloatingOrbs() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      <motion.div
        className="absolute w-[600px] h-[600px] rounded-full opacity-20"
        style={{
          background: 'radial-gradient(circle, hsla(160, 84%, 39%, 0.3) 0%, transparent 70%)',
          top: '-10%',
          right: '-10%',
        }}
        animate={{
          x: [0, 30, -20, 0],
          y: [0, -40, 20, 0],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
      />
      <motion.div
        className="absolute w-[500px] h-[500px] rounded-full opacity-15"
        style={{
          background: 'radial-gradient(circle, hsla(187, 92%, 43%, 0.3) 0%, transparent 70%)',
          bottom: '-5%',
          left: '-5%',
        }}
        animate={{
          x: [0, -30, 20, 0],
          y: [0, 30, -20, 0],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
      />
      <motion.div
        className="absolute w-[300px] h-[300px] rounded-full opacity-10"
        style={{
          background: 'radial-gradient(circle, hsla(217, 91%, 60%, 0.3) 0%, transparent 70%)',
          top: '40%',
          left: '30%',
        }}
        animate={{
          x: [0, 40, -30, 0],
          y: [0, -20, 40, 0],
        }}
        transition={{ duration: 18, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  );
}
