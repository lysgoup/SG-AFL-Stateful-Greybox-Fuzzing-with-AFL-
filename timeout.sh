#!/bin/bash

# Name of your program or command
PROGRAM="../AFLplusplus/afl-fuzz -i ../lys/openssl_probe/fuzz/corpora/server-test -o ../lys/openssl_probe/fuzz/corpora/server-test-out ../lys/openssl_probe/fuzz/server-test @@"

# Time limit in seconds (1 hour = 3600 seconds)
TIME_LIMIT=3700

# Function to handle termination
terminate_program() {
  echo "Terminating the program..."
  kill -SIGTERM "$PROGRAM_PID"
  wait "$PROGRAM_PID"
  exit 1
}

# Trap SIGINT (Ctrl+C)
trap terminate_program SIGINT

# Run the program with a timeout and get its PID
timeout $TIME_LIMIT $PROGRAM &
PROGRAM_PID=$!

# Wait for the program to finish and get its exit status
wait $PROGRAM_PID
EXIT_STATUS=$?

# Check if the program terminated due to the timeout
if [ $EXIT_STATUS -eq 124 ]; then
  echo "The program was terminated after $TIME_LIMIT seconds."
else
  echo "The program completed within the time limit."
fi