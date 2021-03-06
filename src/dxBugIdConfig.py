from dsCdbBinaryPath_sISA import dsCdbBinaryPath_sISA;
# Load base config file
try:
  from dxConfig import dxConfig;
except:
  dxConfig = {};
# Add BugId group if it doesn't exist.
dxBugIdConfig = dxConfig.setdefault("BugId", {});
# Add default values where no values have been supplied:
for (sName, xValue) in {
  ### cdb/kill binary settings
  "sCdbBinaryPath_x86": dsCdbBinaryPath_sISA.get("x86"),
  "sCdbBinaryPath_x64": dsCdbBinaryPath_sISA.get("x64"),
  ### Exception control
  "bIgnoreFirstChanceBreakpoints": False, # When enabled, first chance debugger breakpoints are ignored and only second
                                        # chance debugger breakpoints are analyzed. This speeds up debugging
                                        # considerably, but you risk not detecting some bugs. For instance, application
                                        # verifier signals that it has detected memory corruption with a first chance
                                        # debugger breakpoint, but this exception is handled by verfier and the
                                        # application terminated if this setting is enabled.
  ### Console output
  "bOutputStdIn": False,                # Output cdb input (commands) send to cdb while debugging application
  "bOutputStdOut": False,               # Output cdb output while debugging application
  "bOutputStdErr": True,                # Output cdb error output, which probably comes from the debugged application.
  "bOutputFirstChanceExceptions": False, # Are first chance exceptions detected and output?
  "bOutputCommandLine": False,          # Is the cbd.exe command line printed before execution?
  "bOutputProcesses": True,             # Output process details whenever one is created/attached to/terminated.
  ### Pointer settings
  "uMaxAddressOffset": 0x1000,          # How big an offset from a special address (such as NULL) do you expect in your
                                        # application? Anything within this range from a special address is considered
                                        # to be a pointer to that address + an offset.
  "uMaxOffsetMultiplier": 4,            # Show <address + N> - <address + X * N> where X is this number. Use 0 for
                                        # <address + offset>
  "uMaxFunctionOffset": 0xFFF,          # How big an offset from a function symbol do you expect in your application?
                                        # Anything within this range is considered to be a valid symbol, anything
                                        # further from the symbol is marked as dubious.
  ### Disassembly settings
  "uDisassemblyInstructionsBefore": 0x20, # How many instructions to disassemble before the instruction that triggered
                                        # the crash
  "uDisassemblyInstructionsAfter": 0x10, # How many instructions to disassemble after the instruction that triggered
                                        # the crash
  "uDisassemblyAlignmentBytes": 10,     # How many instructions to start disassembling before the first instruction
                                        # we're interested in, in order to make sure we don't start diassembling in the
                                        # middle of that instruction.
  "uDisassemblyAverageInstructionSize": 4, # Use to guess how many bytes to disassemble to get the requested number of
                                        # instructions
                                        # Note: BugId disassembles A * B + C bytes before and after the instruction
                                        # that triggered the crash, where A is the number of instructions requested, B
                                        # is the average instruction size provided, and C is the number of alignment
                                        # bytes (only used for the "before" instructions, it's 0 for "after"). If
                                        # uDisassemblyAlignmentBytes is too small, the first instruction you see may
                                        # not be an instruction that will ever get executed, as disassembly happed in
                                        # the middle of the "real" instruction. If uDisassemblyAverageInstructionSize
                                        # is too small, you may see less instructions than requested when not enough
                                        # bytes get disassembled to get the requested number of instructions. If the
                                        # total number of bytes disassembled is too large, you may get no disassembly
                                        # at all when part of the memory it attempts to disassemble is not readable.
  ### Stack settings
  "uMaxStackFramesCount": 20,           # How many stack frames are retreived for analysis?
  "uMinStackRecursionLoops": 3,         # How many recursive functions call loops are needed to assume a stack overflow
                                        # is caused by such a loop?
  "uMaxStackRecursionLoopSize": 50,     # The maximum number of functions expected to be in a loop (less increases
                                        # analysis speed, but might miss-analyze a recursion loop involving many
                                        # functions as a simple stack exhaustion). I've seen 43 functions in one loop.
  "uStackHashFramesCount": 2,           # How many stack frames are hashed for the crash id?
  "uMaxStackFrameHashChars": 3,         # How many characters of hash to use in the id for each stack frame.
  ### Symbol loading settings
  "bEnhancedSymbolLoading": True,       # Enable additional checks when getting a stack that can detect and fix errors
                                        # in symbol loading caused by corrupted pdb files. This turns on "noisy symbol
                                        # loading" which may provide useful information to fix symbol loading errors.
                                        # It has a large impact on performance, so you may want to disable it if you
                                        # can guarantee correct symbol files are available and do not need to be
                                        # downloaded (which I think is what sometimes causes this corruption).
  "asSymbolCachePaths": [],             # Where should symbols be cached?
  ### Source code settings
  "bEnableSourceCodeSupport": True,     # Tell cdb to load source line symbols or not.
  "dsURLTemplate_by_srSourceFilePath": {}, # Used to translate source file paths to links to online code repository.
  ### Dump file settings
  "bSaveDump": False,                   # Save a dump file.
  "bOverwriteDump": False,              # Overwrite any existing dump file.
  ### OOM mitigations
  "uReserveRAM": 0,                     # How many bytes of RAM should be allocate at start of debugging, so they can
                                        # be released later to allow analysis under low memory conditions.
  ### Excessive CPU usage detection
  "nExcessiveCPUUsageCheckInterval": 10.0, # How many seconds to gather thread CPU usage data.
  "nExcessiveCPUUsagePercent": 75,      # How long do all threads in all processes for the application need to use the
                                        # CPU during the usage check interval to trigger an excessive CPU usage bug
                                        # report. Value in percent of the check interval, e.g. a value of 75 for a
                                        # check interval of 10s means a bug will be reported if the application uses
                                        # the CPU more than 7.5 seconds during a 10s interval.
  "nExcessiveCPUUsageWormRunTime": 3.0, # How many seconds to allow a function to run to find the topmost function
                                        # involved in the CPU usage? Lower values yield results quicker, but may be
                                        # inaccurate. Higher values increase the time in which the code can run and
                                        # return to the topmost function. If you provide too large a value the CPU
                                        # using loop may finish, giving you invalid results.
  ### Timeouts
  "nTimeoutGranularity": 1.0,           # How often to check for timeouts, in seconds. Making this value smaller causes
                                        # the timeouts to fire closer to the intended time, but slows down debugging.
                                        # Making the value larger can cause timeouts to fire a lot later than requested.
  ### C++ exception handling
  "bIgnoreCPPExceptions": False,        # Can be used to ignore C++ exceptions completely in applications that use them
                                        # a lot. This can speed up debugging quite a bit, but you risk not detecting
                                        # unhandled C++ exceptions. These will cause the application to terminate if
                                        # this setting is enabled, so you may still be able to detect an unhandled C++
                                        # exception through unexpected application termination.
}.items():
  if sName not in dxBugIdConfig:
    dxBugIdConfig[sName] = xValue;
