#This line defines how what name will have output tarball
AC_INIT([CDevelopmentTool],[1.0],[phracek@redhat.com])
#this line defines what compilation flags will be used
AM_INIT_AUTOMAKE([-Wall tar-ustar -Werror])
#this line defines what libraries should be used during building
AC_CHECK_LIB([pthread],[pthread_create])
AC_CHECK_LIB([pthread],[pthread_join])
AC_PROG_CC
AC_PROG_CXX
#This line defines where are stored Makefiles for project and sources
AC_CONFIG_FILES([Makefile src/Makefile])
AC_OUTPUT
