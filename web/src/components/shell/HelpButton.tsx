'use client';

import { type ReactElement, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { HELP_FLOW, HELP_STEPS } from '@/lib/help-steps';

import { CommandBlock } from './CommandBlock';

/** Top-corner Help on the sign-in screen: commands to run the app and test the flow locally. */
export function HelpButton(): ReactElement {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button
        variant="secondary"
        onClick={() => {
          setIsOpen(true);
        }}
      >
        Help
      </Button>
      <Dialog
        isOpen={isOpen}
        title="Run and test GRIT locally"
        size="lg"
        onClose={() => {
          setIsOpen(false);
        }}
      >
        <ol className="flex flex-col gap-5">
          {HELP_STEPS.map((step, index) => (
            <li key={step.title} className="flex flex-col gap-2">
              <h3 className="text-base font-semibold">
                {index + 1}. {step.title}
              </h3>
              {step.note ? <p className="text-sm text-muted">{step.note}</p> : null}
              {step.commands.map((command) => (
                <CommandBlock key={command} command={command} />
              ))}
            </li>
          ))}
          <li className="flex flex-col gap-2">
            <h3 className="text-base font-semibold">{HELP_STEPS.length + 1}. Test the flow</h3>
            <ol className="list-decimal space-y-1 pl-5 text-sm text-ink-soft">
              {HELP_FLOW.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ol>
          </li>
        </ol>
        <div className="mt-6 flex justify-end">
          <Button
            variant="secondary"
            onClick={() => {
              setIsOpen(false);
            }}
          >
            Close
          </Button>
        </div>
      </Dialog>
    </>
  );
}
