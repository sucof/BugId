import os, re, sys, threading;

bDebugStartFinish = False;  # Show some output when a test starts and finishes.
bDebugIO = False;           # Show cdb I/O during tests (you'll want to run only 1 test at a time for this).
uSequentialTests = 32;      # Run multiple tests simultaniously, values >32 will probably not work.
if bDebugIO: uSequentialTests = 1; # prevent UI mess

from dxConfig import dxConfig;
dxBugIdConfig = dxConfig["BugId"];
dxBugIdConfig["bOutputStdIn"] = \
    dxBugIdConfig["bOutputStdOut"] = \
    dxBugIdConfig["bOutputStdErr"] = bDebugIO;
dxBugIdConfig["bOutputProcesses"] = False;
dxBugIdConfig["uReserveRAM"] = 1024; # Simply test if reserving RAM works, not actually reserve any useful amount.

sBaseFolderPath = os.path.dirname(__file__);
sys.path.extend([os.path.join(sBaseFolderPath, x) for x in ["src", "modules"]]);
from cBugId import cBugId;
from sOSISA import sOSISA;
from cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION import ddtsDetails_uAddress_sISA;
from fsCreateFileName import fsCreateFileName;

asTestISAs = [sOSISA];
if sOSISA == "x64":
  asTestISAs.append("x86");

sBaseFolderPath = os.path.dirname(__file__);
dsBinaries_by_sISA = {
  "x86": os.path.join(sBaseFolderPath, r"Tests\bin\Tests_x86.exe"),
  "x64": os.path.join(sBaseFolderPath, r"Tests\bin\Tests_x64.exe"),
};

bFailed = False;
oOutputLock = threading.Lock();
# If you see weird exceptions, try lowering the number of parallel tests:
oConcurrentTestsSemaphore = threading.Semaphore(uSequentialTests);
class cTest(object):
  def __init__(oTest, sISA, asCommandLineArguments, sExpectedBugTypeId):
    oTest.sISA = sISA;
    oTest.asCommandLineArguments = asCommandLineArguments;
    oTest.sExpectedBugTypeId = sExpectedBugTypeId;
    oTest.bInternalException = False;
    oTest.bHasOutputLock = False;
  
  def __str__(oTest):
    return "%s =%s=> %s" % (" ".join(oTest.asCommandLineArguments), oTest.sISA, oTest.sExpectedBugTypeId);
  
  def fRun(oTest):
    global bFailed, oOutputLock;
    oConcurrentTestsSemaphore.acquire();
    sBinary = dsBinaries_by_sISA[oTest.sISA];
    asApplicationCommandLine = [sBinary] + oTest.asCommandLineArguments;
    if bDebugStartFinish:
      oOutputLock and oOutputLock.acquire();
      oTest.bHasOutputLock = True;
      print "@ Started %s" % oTest;
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
    try:
      oTest.oBugId = cBugId(
        asApplicationCommandLine = asApplicationCommandLine,
        asSymbolServerURLs = ["http://msdl.microsoft.com/download/symbols"],
        bGetDetailsHTML = dxConfig["bSaveTestReports"],
        fFinishedCallback = oTest.fFinishedHandler,
        fInternalExceptionCallback = oTest.fInternalExceptionHandler,
      );
      oTest.oBugId.fSetCheckForExcessiveCPUUsageTimeout(1);
    except Exception, oException:
      if not bFailed:
        bFailed = True;
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
        print "- Failed test: %s" " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
        print "  Expected:    %s" % oTest.sExpectedBugTypeId;
        print "  Exception:   %s" % oException;
        oOutputLock and oOutputLock.release();
        oTest.bHasOutputLock = False;
  
  def fWait(oTest):
    hasattr(oTest, "oBugId") and oTest.oBugId.fWait();
  
  def fFinished(oTest):
    if bDebugStartFinish:
      oOutputLock and oOutputLock.acquire();
      oTest.bHasOutputLock = True;
      print "@ Finished %s" % oTest;
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
    oConcurrentTestsSemaphore.release();
  
  def fFinishedHandler(oTest, oBugReport):
    global bFailed, oOutputLock;
    if not bFailed:
      oOutputLock and oOutputLock.acquire();
      oTest.bHasOutputLock = True;
      if oTest.sExpectedBugTypeId:
        if not oBugReport:
          print "- Failed test: %s" " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
          print "  Expected:    %s" % oTest.sExpectedBugTypeId;
          print "  Got nothing";
          bFailed = True;
        elif not oTest.sExpectedBugTypeId == oBugReport.sBugTypeId:
          print "- Failed test: %s" " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
          print "  Expected:    %s" % oTest.sExpectedBugTypeId;
          print "  Reported:    %s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
          print "               %s" % (oBugReport.sBugDescription);
          bFailed = True;
        else:
          print "+ %s" % oTest;
      elif oBugReport:
        print "- Failed test: %s" " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
        print "  Expected no report";
        print "  Reported:    %s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
        print "               %s" % (oBugReport.sBugDescription);
        bFailed = True;
      else:
        print "+ %s" % oTest;
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
      if dxConfig["bSaveTestReports"] and oBugReport:
        sFileNameBase = fsCreateFileName("%s = %s" % (oTest, oBugReport.sId));
        # File name may be too long, keep trying to save it with a shorter name or output an error if that's not possible.
        while len(sFileNameBase) > 0:
          sFilePath = os.path.join(os.path.dirname(__file__), "Test reports", "%s.html" % sFileNameBase);
          try:
            oFile = open(sFilePath, "wb");
          except IOError:
            sFileNameBase = sFileNameBase[:-1];
            continue;
          try:
            oFile.write(oBugReport.sDetailsHTML);
          finally:
            oFile.close();
          break;
        else:
          oOutputLock and oOutputLock.acquire();
          oTest.bHasOutputLock = True;
          print "  - Bug report cannot be saved";
          bFailed = True;
          oOutputLock and oOutputLock.release();
          oTest.bHasOutputLock = False;
    oTest.fFinished();
    oTest.bHandlingResult = False;
  
  def fInternalExceptionHandler(oTest, oException):
    global bFailed;
    oTest.fFinished();
    if not bFailed:
      # Exception in fFinishedHandler can cause this function to be executed with lock still in place.
      if not oTest.bHasOutputLock:
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
      bFailed = True;
      print "@ Exception in %s: %s" % (oTest, oException);
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
      raise;

if __name__ == "__main__":
  if sys.argv[1:2] == ["--save-reports"]:
    dxConfig["bSaveTestReports"] = True;
  
  aoTests = [];
  for sISA in asTestISAs:
    aoTests.append(cTest(sISA, ["Nop"], None)); # No exceptions, just a clean program exit.
    aoTests.append(cTest(sISA, ["CPUUsage"], "CPUUsage"));
    sMinusOne = {"x86": "FFFFFFFF", "x64": "FFFFFFFFFFFFFFFF"}[sISA];
    sMinusTwo = {"x86": "FFFFFFFE", "x64": "FFFFFFFFFFFFFFFE"}[sISA];
    aoTests.append(cTest(sISA, ["AccessViolation", "READ", "1"], "AVR:NULL+N"));
    aoTests.append(cTest(sISA, ["AccessViolation", "READ", "2"], "AVR:NULL+2*N"));
    aoTests.append(cTest(sISA, ["AccessViolation", "READ", "3"], "AVR:NULL+N"));
    aoTests.append(cTest(sISA, ["AccessViolation", "READ", "4"], "AVR:NULL+4*N"));
    aoTests.append(cTest(sISA, ["AccessViolation", "READ", "5"], "AVR:NULL+N"));
    if sISA != "x64": # Does not work on x64 dues to limitations of exception handling (See foAnalyzeException_STATUS_ACCESS_VIOLATION for details).
      aoTests.append(cTest(sISA, ["AccessViolation", "READ", sMinusOne], "AVR:NULL-N"));
    aoTests.append(cTest(sISA, ["AccessViolation", "READ", sMinusTwo], "AVR:NULL-2*N"));
    aoTests.append(cTest(sISA, ["Breakpoint"], "Breakpoint"));
    aoTests.append(cTest(sISA, ["C++"], "C++:cException"));
    aoTests.append(cTest(sISA, ["IntegerDivideByZero"], "IntegerDivideByZero"));
    aoTests.append(cTest(sISA, ["Numbered", "41414141", "42424242"], "0x41414141"));
    # Specific test to check for ntdll!RaiseException exception address being off-by-one from the stack address:
    aoTests.append(cTest(sISA, ["Numbered", "80000003", "1"], "Breakpoint"));
    aoTests.append(cTest(sISA, ["IllegalInstruction"], "IllegalInstruction"));
    aoTests.append(cTest(sISA, ["PrivilegedInstruction"], "PrivilegedInstruction"));
    aoTests.append(cTest(sISA, ["StackExhaustion"], "StackExhaustion"));
    aoTests.append(cTest(sISA, ["RecursiveCall"], "RecursiveCall"));
    aoTests.append(cTest(sISA, ["StaticBufferOverrun10", "Write", "20"], "FailFast2:StackCookie"));
    aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "-1"], "HeapCorrupt"));  # Write the byte at offset -1 from the start of the buffer.
    aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "d"], "HeapCorrupt"));   # Write the byte at offset 0 from the end of the buffer.
    if sISA not in ["x86"]:
      # x86 test results in "0BA2 FailFast2:AppExit Tests_x86.exe!abort (A critical issue was detected (code C0000409, fail fast code 7: FAST_FAIL_FATAL_APP_EXIT))"
      aoTests.append(cTest(sISA, ["PureCall"], "PureCall"));
      # Page heap does not appear to work for x86 tests on x64 platform.
      aoTests.append(cTest(sISA, ["UseAfterFree", "Read", "20", "0"], "AVR:Free"));
      aoTests.append(cTest(sISA, ["UseAfterFree", "Write", "20", "0"], "AVW:Free"));
      aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", "20", "4"], "AVR:OOB+4*N"));
      aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", "20", "4"], "AVW:OOB+4*N"));
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "10"], "AVR:OOB+4*N"));   # Read byte at offset 4 from the end of the memory block
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "11"], "AVR:OOB+N"));     # Read byte at offset 5 from the end of the memory block
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "12"], "AVR:OOB+2*N"));   # Read byte at offset 6 from the end of the memory block
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "13"], "AVR:OOB+N"));     # Read byte at offset 7 from the end of the memory block
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "10"], "AVW:OOB+4*N"));  # Write byte at offset 4 from the end of the memory block
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "11"], "AVW:OOB+N"));    # Write byte at offset 5 from the end of the memory block
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "12"], "AVW:OOB+2*N"));  # Write byte at offset 6 from the end of the memory block
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "13"], "AVW:OOB+N"));    # Write byte at offset 7 from the end of the memory block
    if False:
      # This does not appear to work at all. TODO: fix this.
      aoTests.append(cTest(sISA, ["BufferOverrun", "Stack", "Write", "20", "1000"], "AVW:OOB"));
    
    for (uBaseAddress, sDescription) in [
      # 0123456789ABCDEF
             (0x60000000, "Unallocated"), # This is not guaranteed; this test may fail by chance
            (0x100000000, "Unallocated"), # This is not guaranteed; this test may fail by chance
         (0x7ffffffd0000, "Unallocated"),
         (0x7ffffffdffff, "Unallocated"),
         (0x7ffffffe0000, "Reserved"),
         (0x7ffffffeffff, "Reserved"),
         (0x7fffffff0000, "Unallocated"),
         (0x7fffffffffff, "Unallocated"),
         (0x800000000000, "Invalid"),
     (0x8000000000000000, "Invalid"),
    ]:
      if uBaseAddress < (1 << 32) or sISA == "x64":
        # On x64, there are some limitations to exceptions occoring at addresses between the userland and kernelland
        # memory address ranges.
        if uBaseAddress >= 0x800000000000 and uBaseAddress < 0xffff800000000000:
          aoTests.extend([
            cTest(sISA, ["AccessViolation", "Read", "%X" % uBaseAddress], "AV?:%s" % sDescription),
            cTest(sISA, ["AccessViolation", "Write", "%X" % uBaseAddress], "AV?:%s" % sDescription),
          ]);
        else:
          aoTests.extend([
            cTest(sISA, ["AccessViolation", "Read", "%X" % uBaseAddress], "AVR:%s" % sDescription),
            cTest(sISA, ["AccessViolation", "Write", "%X" % uBaseAddress], "AVW:%s" % sDescription),
          ]);
        cTest(sISA, ["AccessViolation", "Call", "%X" % uBaseAddress], "AVE:%s" % sDescription),
        cTest(sISA, ["AccessViolation", "Jump", "%X" % uBaseAddress], "AVE:%s" % sDescription),
  
  for (sISA, dtsDetails_uAddress) in ddtsDetails_uAddress_sISA.items():
    for (uBaseAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uAddress.items():
      if uBaseAddress < (1 << 32) or (sISA == "x64" and uBaseAddress < (1 << 47)):
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "%X" % uBaseAddress], "AVR:%s" % sAddressId));
        aoTests.append(cTest(sISA, ["AccessViolation", "Write", "%X" % uBaseAddress], "AVW:%s" % sAddressId));
        aoTests.append(cTest(sISA, ["AccessViolation", "Call", "%X" % uBaseAddress], "AVE:%s" % sAddressId));
        aoTests.append(cTest(sISA, ["AccessViolation", "Jump", "%X" % uBaseAddress], "AVE:%s" % sAddressId));
      elif sISA == "x64":
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "%X" % uBaseAddress], "AV?:%s" % sAddressId));
        aoTests.append(cTest(sISA, ["AccessViolation", "Write", "%X" % uBaseAddress], "AV?:%s" % sAddressId));
        aoTests.append(cTest(sISA, ["AccessViolation", "Call", "%X" % uBaseAddress], "AVE:%s" % sAddressId));
        aoTests.append(cTest(sISA, ["AccessViolation", "Jump", "%X" % uBaseAddress], "AVE:%s" % sAddressId));
  
  print "* Starting tests...";
  for oTest in aoTests:
    if bFailed:
      break;
    oTest.fRun();
  for oTest in aoTests:
    oTest.fWait();
  
  oOutputLock.acquire();
  if bFailed:
    print "* Tests failed."
    sys.exit(1);
  else:
    print "* All tests passed!"
    sys.exit(0);
