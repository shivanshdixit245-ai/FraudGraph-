import React from 'react';
import useStore from './store';
import { WifiOff } from 'lucide-react';

export default function StatusBanner() {
  const wsStatus = useStore(state => state.wsStatus);
  const isDemo = useStore(state => state.isDemo);
  const [shouldShow, setShouldShow] = React.useState(false);

  React.useEffect(() => {
    let timer;
    if (wsStatus !== 'connected') {
      // Debounce the error message to avoid blinking on quick navigations/reconnects
      timer = setTimeout(() => setShouldShow(true), 500);
    } else {
      setShouldShow(false);
    }
    return () => clearTimeout(timer);
  }, [wsStatus]);

  if (!shouldShow && !isDemo) return null;

  return (
    <div className="flex flex-col w-full relative z-50">
      {shouldShow && wsStatus !== 'connected' && (
        <div className="bg-[#E24B4A] text-[#E6EDF3] px-4 py-2 flex items-center justify-center space-x-2 text-sm font-medium animate-[slideDown_0.3s_ease-out] shadow-md">
          <WifiOff className="w-4 h-4" />
          <span>
            {wsStatus === 'reconnecting' 
              ? 'WebSocket connection lost. Attempting to reconnect...' 
              : 'WebSocket disconnected. Real-time updates paused.'}
          </span>
        </div>
      )}
      {isDemo && (
        <div className="bg-[#EF9F27]/10 border-b border-[#EF9F27]/30 text-[#EF9F27] px-4 py-1 flex items-center justify-center text-xs font-medium font-['Inter'] shadow-sm">
          <span>Live backend offline — showing demo data</span>
        </div>
      )}
    </div>
  );
}
