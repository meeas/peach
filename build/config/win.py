import os, os.path, platform
from waflib import Utils, Errors
from waflib.TaskGen import feature

host_plat = [ 'win32' ]

archs = [ 'x86', 'x64' ]

tools = [
	'msvc',
	'cs',
	'resx',
	'midl',
	'misc',
	'tools.msbuild',
	'tools.utils',
	'tools.externals',
	'tools.test',
	'tools.version',
	'tools.mdoc',
	'tools.wix',
	'tools.zip',
]

def prepare(conf):
	env = conf.env
	j = os.path.join

	env['MSVC_VERSIONS'] = ['msvc 10.0', 'wsdk 7.1', 'msvc 11.0', 'msvc 12.0']
	env['MSVC_TARGETS']  = 'x64' in env.SUBARCH and [ 'x64', 'x86_amd64' ] or [ 'x86' ]

	env['PIN_VER'] = 'pin-2.13-61206-msvc10-windows'

	pin = j(conf.get_peach_dir(), '3rdParty', 'pin', env['PIN_VER'])

	env['EXTERNALS_x86'] = {
		'pin' : {
			'MSVC'      : [ 'msvc 10.0', 'wsdk 7.1' ], 
			'INCLUDES'  : [
				j(pin, 'source', 'include', 'pin'),
				j(pin, 'source', 'include', 'pin', 'gen'),
				j(pin, 'extras', 'components', 'include'),
				j(pin, 'extras', 'xed2-ia32', 'include'),
			],
			'HEADERS'   : [],
			'STLIBPATH' : [
				j(pin, 'ia32', 'lib'),
				j(pin, 'ia32', 'lib-ext'),
				j(pin, 'extras', 'xed2-ia32', 'lib'),
			],
			'STLIB'     : [ 'pin', 'ntdll-32', 'pinvm', 'libxed' ],
			'DEFINES'   : [ 'BIGARRAY_MULTIPLIER=1', '_SECURE_SCL=0', 'TARGET_WINDOWS', 'TARGET_IA32', 'HOST_IA32', 'USING_XED', ],
			'CFLAGS'    : [ '/MT' ],
			'CXXFLAGS'  : [ '/MT' ],
			'LINKFLAGS' : [ '/EXPORT:main', '/ENTRY:Ptrace_DllMainCRTStartup@12', '/BASE:0x55000000' ],
		},
		'com' : {
			'HEADERS' : [ 'atlbase.h' ],
			'DEFINES' : [ '_WINDLL' ],
		},
		'network' : {
			'HEADERS' : [ 'winsock2.h' ],
			'STLIB'   : [ 'ws2_32' ],
		},
	}

	env['EXTERNALS_x64'] = {
		'pin' : {
			'MSVC'      : [ 'msvc 10.0', 'wsdk 7.1' ], 
			'INCLUDES'  : [
				j(pin, 'source', 'include', 'pin'),
				j(pin, 'source', 'include', 'pin', 'gen'),
				j(pin, 'extras', 'components', 'include'),
				j(pin, 'extras', 'xed2-intel64', 'include'),
			],
			'HEADERS'   : [],
			'STLIBPATH'   : [
				j(pin, 'intel64', 'lib'),
				j(pin, 'intel64', 'lib-ext'),
				j(pin, 'extras', 'xed2-intel64', 'lib'),
			],
			'STLIB'     : [ 'pin', 'ntdll-64', 'pinvm', 'libxed' ],
			'DEFINES'   : [ 'BIGARRAY_MULTIPLIER=1', '_SECURE_SCL=0', 'TARGET_WINDOWS', 'TARGET_IA32E', 'HOST_IA32E', 'USING_XED', ],
			'CFLAGS'    : [ '/MT' ],
			'CXXFLAGS'  : [ '/MT' ],
			'LINKFLAGS' : [ '/EXPORT:main', '/ENTRY:Ptrace_DllMainCRTStartup', '/BASE:0xC5000000' ],
		},
		'com' : {
			'HEADERS' : [ 'atlbase.h' ],
			'DEFINES' : [ '_WINDLL' ],
		},
		'network' : {
			'HEADERS' : [ 'winsock2.h' ],
			'STLIB'   : [ 'ws2_32' ],
		},
	}

	env['EXTERNALS'] = env['EXTERNALS_%s' % env.SUBARCH]

	# This is lame, the resgen that vcvars for x64 finds is the .net framework 3.5 version.
	# The .net 4 version is in the x86 search path.
	if env.SUBARCH == 'x64':
		env['MCS'] = getattr(conf.all_envs.get('win_x86'), 'MCS', None)
		env['RESGEN'] = getattr(conf.all_envs.get('win_x86'), 'RESGEN', None)

	pfiles = os.getenv('PROGRAMFILES(X86)', os.getenv('PROGRAMFILES'))
	env['TARGET_FRAMEWORK'] = 'v4.0'
	env['TARGET_FRAMEWORK_NAME'] = '.NET Framework 4'
	env['REFERENCE_ASSEMBLIES'] = j(pfiles, 'Reference Assemblies', 'Microsoft', 'Framework', '.NETFramework', env['TARGET_FRAMEWORK'])

def configure(conf):
	conf.ensure_version('CXX', ['16.00.40219.01', '17.00.61030', '18.00.21005.1'])

	env = conf.env

	# Ensure reference assembly folder exists
	if not os.path.isdir(env.REFERENCE_ASSEMBLIES):
		raise Errors.WafError("Could locate .NET Framework %s reference assemblies in: %s" % (env.TARGET_FRAMEWORK, env.REFERENCE_ASSEMBLIES))

	# Make sure all ASSEMBLY entries are fully pathed
	env.ASS_ST = '/reference:%s%s%%s' % (env.REFERENCE_ASSEMBLIES, os.sep)

	env.append_value('supported_features', [
		'win',
		'c',
		'cstlib',
		'cshlib',
		'cprogram',
		'cxx',
		'cxxstlib',
		'cxxshlib',
		'cxxprogram',
		'fake_lib',
		'cs',
		'debug',
		'release',
		'emit',
		'vnum',
		'subst',
		'msbuild',
	])

	cppflags = [
		'/Z7',
		'/W4',
		'/WX',
	]

	cppflags_debug = [
		'/MTd',
		'/Od',
	]

	cppflags_release = [
		'/MT',
		'/Ox',
	]

	env.append_value('CPPFLAGS', cppflags)
	env.append_value('CPPFLAGS_debug', cppflags_debug)
	env.append_value('CPPFLAGS_release', cppflags_release)

	env.append_value('CXXFLAGS', [ '/EHsc' ])

	env.append_value('DEFINES', [
		'WIN32',
		'_CRT_SECURE_NO_WARNINGS',
	])

	env.append_value('DEFINES_debug', [
		'DEBUG',
		'_DEBUG',
	])

	env.append_value('CSFLAGS', [
		'/noconfig',
		'/nologo',
		'/nostdlib+',
		'/warn:4',
		'/define:PEACH',
		'/errorreport:prompt',
		'/warnaserror',
		'/nowarn:1591', # Missing XML comment for publicly visible type
	])

	env.append_value('CSFLAGS_debug', [
		'/define:DEBUG;TRACE',
	])

	env.append_value('CSFLAGS_release', [
		'/define:TRACE',
		'/optimize+',
	])

	env.append_value('ASSEMBLIES', [
		'mscorlib.dll',
	])

	env.append_value('LINKFLAGS', [
		'/NOLOGO',
		'/DEBUG',
		'/INCREMENTAL:NO',
		'/WX',
	])

	env['CSPLATFORM'] = env.SUBARCH
	env['CSDOC'] = True

	env.append_value('MIDLFLAGS', [
		'/%s' % ('x86' in env.SUBARCH and 'win32' or 'amd64'),
	])

	env['VARIANTS'] = [ 'debug', 'release' ]

def debug(env):
	env.CSDEBUG = 'full'

def release(env):
	env.CSDEBUG = 'pdbonly'
