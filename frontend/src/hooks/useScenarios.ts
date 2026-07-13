import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { scenarioService } from '@/services/scenario.service';
import type { CreateScenarioDTO, UpdateScenarioDTO } from '@/types/scenario';
import { toast } from 'sonner';

const CACHE_KEY = ['scenarios'];

export const useScenarios = () => {
  return useQuery({
    queryKey: CACHE_KEY,
    queryFn: scenarioService.getScenarios,
  });
};

export const useScenario = (id: number) => {
  return useQuery({
    queryKey: [...CACHE_KEY, id],
    queryFn: () => scenarioService.getScenario(id),
    enabled: !!id,
  });
};

export const useCreateScenario = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateScenarioDTO) => scenarioService.createScenario(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEY });
      toast.success('Scenario created successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create scenario');
    },
  });
};

export const useUpdateScenario = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateScenarioDTO }) =>
      scenarioService.updateScenario(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEY });
      toast.success('Scenario updated successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update scenario');
    },
  });
};

export const useDeleteScenario = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => scenarioService.deleteScenario(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEY });
      toast.success('Scenario deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete scenario');
    },
  });
};
