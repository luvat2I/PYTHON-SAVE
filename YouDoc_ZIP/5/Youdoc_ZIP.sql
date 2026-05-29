/****** Object:  Table [dbo].[framework_ost_document]    Script Date: 09/01/2026 09:01:45 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[zip_document](
	[object_id_zip] [varchar](128) NOT NULL,
	[object_id] [varchar](128) NOT NULL,
	[media_type] [varchar](255) NULL,
	[path_and_file_name] [varchar](1024) NULL,
	[STATUS] [char](1) NOT NULL
) ON [PRIMARY]
GO