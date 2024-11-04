from dataclasses import dataclass
import os
from python.helpers.shell_local import LocalInteractiveSession
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.docker import DockerContainerManager
from agent import Agent

@dataclass
class State:
    docker: DockerContainerManager | None
    shell: LocalInteractiveSession | None

class FileWriter(Tool):

	async def execute(self, **kwargs):
		# Log kwargs to avoid unused variable warning
		self.agent.context.log.log(type="info", heading="execute kwargs", content=str(kwargs))
		
		await self.agent.handle_intervention()  # Handle any intervention if paused
		await self.prepare_state()

		file_path = self.args.get("filename")
		content = self.args.get("content")
		folder_path = self.args.get("folder")
		
		if not file_path or not content or not folder_path:
			response = "Filename, folder, or content not provided."
			return Response(message=response, break_loop=False)

		if '/' in file_path:
			response = "File name should not contain '/'."
			return Response(message=response, break_loop=False)

		if '..' in folder_path:
			response = "Folder path should not contain '..'."
			return Response(message=response, break_loop=False)

		try:
			# Write content to the local file
			abs_path = os.path.abspath('work_dir')

			os.makedirs(os.path.join(abs_path,folder_path), exist_ok=True)
			if folder_path == '.':
				folder_path = ''
			remote_path = os.path.join(folder_path,file_path)
			with open(os.path.join(abs_path,remote_path), 'w') as file:
				file.write(content)

			await self.transfer_file_to_docker(os.path.join(abs_path, folder_path,file_path), '/root/'+remote_path)

			response = f"File written successfully at {remote_path}."
		except Exception as e:
			response = f"Error writing file: {e}"

		return Response(message=response, break_loop=False)

	async def transfer_file_to_docker(self, local_path, remote_path):
		try:
			# Use Docker copy instead of SSH/SCP
			if not self.state.docker:
				raise ValueError("Docker container manager is not initialized.")
			
			self.state.docker.copy_to_container(local_path, remote_path)
			PrintStyle(font_color="#1B4F72", bold=True).print(
				f"File transferred to Docker container at {remote_path}."
			)
		except Exception as e:
			PrintStyle(font_color="red", bold=True).print(
				f"Error transferring file to Docker container: {e}"
			)
			self.agent.context.log.log(type="error", heading="Docker Copy Error", content=str(e))

	async def prepare_state(self, reset=False):
		self.state = self.agent.get_data("cot_state")
		if not self.state or reset:
			# Initialize Docker container if execution in Docker is configured
			if self.agent.config.code_exec_docker_enabled:
				docker = DockerContainerManager(
					logger=self.agent.context.log,
					name=self.agent.config.code_exec_docker_name,
					image=self.agent.config.code_exec_docker_image,
					ports=self.agent.config.code_exec_docker_ports,
					volumes=self.agent.config.code_exec_docker_volumes,
				)
				docker.start_container()
			else:
				docker = None

			# Initialize local shell interface
			shell = LocalInteractiveSession()

			self.state = State(shell=shell, docker=docker)
			await shell.connect()
		self.agent.set_data("cot_state", self.state)

	async def before_execution(self, **kwargs):
		# Log kwargs to avoid unused variable warning
		self.agent.context.log.log(type="info", heading="before_execution kwargs", content="str(kwargs)")
		
		await self.agent.handle_intervention()  # Handle any intervention if paused
		PrintStyle(
			font_color="#1B4F72", padding=True, background_color="white", bold=True
		).print(f"{self.agent.agent_name}: Using tool '{self.name}'")
		self.log = self.agent.context.log.log(
			type="info",
			heading=f"{self.agent.agent_name}: Using tool '{self.name}'",
			content="",
			kvps=self.args,
		)
		if self.args and isinstance(self.args, dict):
			for key, value in self.args.items():
				PrintStyle(font_color="#85C1E9", bold=True).stream(
					self.nice_key(key) + ": "
				)
				PrintStyle(
					font_color="#85C1E9",
					padding=isinstance(value, str) and "\n" in value,
				).stream(value)
				PrintStyle().print()

	async def after_execution(self, response, **kwargs):
		
		msg_response = self.agent.read_prompt(
			"fw.tool_response.md", tool_name=self.name, tool_response=response.message
		)
		await self.agent.append_message(msg_response, human=False)
