# Copyright (C) 2019 Wuming Liu (lwmqwer@163.com)

AC_PREREQ([2.69])
AC_INIT([UDPAdapter], [0.1], [lwmqwer@163.com])
AC_CONFIG_HEADERS([config.h])

# Checks for programs.
AC_PROG_CC

# Checks for libraries.

# Checks for header files.
AC_CHECK_HEADERS([arpa/inet.h netinet/in.h stdlib.h sys/socket.h])

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.
AC_CHECK_FUNCS([inet_ntoa socket])

AM_INIT_AUTOMAKE([foreign subdir-objects])
AC_CONFIG_FILES([Makefile src/Makefile])
AC_OUTPUT
